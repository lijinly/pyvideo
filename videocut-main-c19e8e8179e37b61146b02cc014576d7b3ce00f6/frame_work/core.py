import os
from typing import List
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser,PydanticOutputParser
from pydantic import BaseModel, Field


# 加载环境变量（存储 OpenAI API Key）
load_dotenv()
os.environ["dashscope_api_key"] = os.getenv("OPENAI_API_KEY")

class context:
    def __init__(self):
         
        # 大模型客户端（基于 LangChain 封装）
        # temperature=0.3 保证输出更精准
        api_key = os.getenv("dashscope_api_key")
        base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        
        self.exec_llm = ChatOpenAI(model_name="qwen-max-latest", 
                                    temperature=0.3,
                                    openai_api_key=api_key,  
                                    openai_api_base=base_url,                      
                                    timeout=60 
                                    )  
        
        self.eval_llm = ChatOpenAI(model_name="qwen-max-latest", 
                                    temperature=0.3,
                                    openai_api_key=api_key,  
                                    openai_api_base=base_url,                      
                                    timeout=60  
                                    )
        
        self.plan = plan_stage(llm= self.exec_llm)
        self.execution = execute_stage(llm= self.exec_llm)
        self.feedback = feedback_stage(llm= self.eval_llm)
        self.optimization = optimize_stage(llm= self.exec_llm)
    
   
     
    # def main(self):
    #     print("=== LangChain 驱动的规划-执行-反馈闭环 ===")
    #     # 任务参数（竞品分析场景）
    #     goal = "3天内完成XX产品的市场竞品分析报告"
    #     constraints = "聚焦价格/功能/用户评价；近6个月公开数据；每日耗时≤8小时"
    #     output_std = "含5家竞品对比表（Markdown）+ 200字结论；输出为Word文档"

    #     # 执行闭环
    #     confirmed_plan = self.plan.execute(goal, constraints, output_std)
    #     execution_result = self.execution.execute(confirmed_plan)
    #     feedback_report = self.feedback.execute(goal, output_std, execution_result)
    #     self.optimization.execute(feedback_report)

    #     print("\n=== 全流程结束 ===")

class plan_stage:
    """
    规划阶段：LangChain 驱动任务拆解
    """
    def __init__(self,llm):
    
        self.llm = llm
       
        self.prompt_text_template = PromptTemplate( 
            input_variables=["goal", "constraints", "output_std", "optimization_rules"],
            template="""
            你是专业的任务规划师，请基于以下信息生成详细的任务规划方案：
            1. 核心目标：{goal}
            2. 约束条件：{constraints}
            3. 输出标准：{output_std}
            4. 优化规则：{optimization_rules}
            
            规划方案需包含三部分，用清晰结构输出：
            - 【每日任务清单】：按时间排序，明确每个任务的「输出物」和「预估耗时」；
            - 【资源需求】：完成任务需用到的工具、数据来源等；
            - 【风险预判】：可能遇到的问题及初步应对方案。
            
            请参考提供的优化规则来改进规划方案。
            """
        )
       
     
    def execute(self,goal:str,constraints:str,output_std:str,optimization_rules:str,human_adjust:str=None):
        """
        通过 LangChain PromptTemplate 生成规划，人工确认后返回
        """     
        
        # 1. 格式化 Prompt 并调用大模型
        formatted_planning_prompt = self.prompt_text_template.format(
            goal=goal, 
            constraints=constraints, 
            output_std=output_std,
            optimization_rules=optimization_rules
        )
        
        plan_text = self.llm([HumanMessage(content=formatted_planning_prompt)]).content

        if not human_adjust:
            return {"plan_text": plan_text, "is_confirmed": False}
        else:             
            adjusted_prompt = f"{formatted_planning_prompt}\n按以下要求调整：{human_adjust}"       
            plan_text = self.llm([HumanMessage(content=adjusted_prompt)]).content 
            return {"plan_text": plan_text, "is_confirmed": True}

class _execute_output_task(BaseModel):
    id: str = Field(description="任务编号")
    content: str = Field(description="任务内容")
    output: str = Field(description="输出格式")

# 2. 再定义整个输出响应的模型，其核心是一个Book类型的列表
class _execute_output_task_list(BaseModel):
    tasks: List[_execute_output_task] = Field(description="任务列表")
    
    
class execute_stage:  
  
    
    """
    执行阶段：人机协同任务落地
    """
    def __init__(self,llm):
        self.llm = llm
        
        parser = PydanticOutputParser(pydantic_object= _execute_output_task_list )
        
        self.prompt_text_template = PromptTemplate(
            input_variables=["plan_text"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
            template="""
            从以下规划方案中，提取「大模型可直接完成的标准化任务」（如信息整理、表格生成、格式处理），
            并按照「任务编号」进行编号，输出为「任务清单」，
            每条任务需明确「任务编号」、「任务内容」和「输出要求」：
            规划方案：{plan_text}
            请根据用户请求生成一个JSON列表。
            \n{format_instructions}\n
            """
            )
    

    def execute(self,confirmed_plan):
        """
        LangChain 提取并执行标准化任务，人工处理决策性工作
        """
        
        execution_result = {"llm_tasks": [], "human_tasks": [], "issues": []}

        # 1. 提取大模型任务（用 LangChain Prompt 格式化）
        formatted_extract_prompt = self.prompt_text_template.format(plan_text=confirmed_plan["plan_text"])
        llm_task_list = self.llm([HumanMessage(content=formatted_extract_prompt)]).content      

        # TO-DO：
        # 准备集成 mcp 服务
        for task in  llm_task_list:
            task_content = task["任务内容"]
            task_output = task["输出要求"]
            task_text =f"任务内容:{task_content},输出要求:{task_output}"          
            task_output = self.llm([HumanMessage(content=f"完成任务：{task_text}")]).content
            execution_result["llm_tasks"].append({"task": task["任务编号"], "output": task_output})
            
  
        # 3. 人工任务处理（模拟）
        human_task = "确认竞品名单+补充内部销售数据"
        execution_result["human_tasks"].append({
            "task": human_task,
            "output": input(f"\n输入人工任务「{human_task}」结果：")
        })

        # 4. 动态处理问题（模拟）
        if input("\n执行中是否有问题？（y/n）：").lower() == "y":
            issue = input("描述问题：")
            solution = self.llm([HumanMessage(content=f"解决执行问题：{issue}，现有资源：{execution_result['human_tasks'][0]['output']}")]).content
            execution_result["issues"].append({"issue": issue, "solution": solution})
            print(f"\n问题解决方案：{solution}")

        return execution_result
    
class feedback_stage:
    """
    反馈阶段：结果校验与归因
    """
    def __init__(self,llm):
        self.llm = llm
        self.prompt_text_template = PromptTemplate(
            input_variables=["goal", "output_std", "execution_result", "human_feedback"],
            template="""
            你是结果校验与分析专家，请完成以下工作：
            1. 对照目标校验：原始目标={goal}，输出标准={output_std}，执行结果={execution_result}
            2. 结合人工反馈：{human_feedback}
            3. 输出两部分内容：
            - 【校验结论】：符合项、偏差项（明确缺失/错误）；
            - 【问题归因】：按「规划层/执行层/外部问题」分类，说明根源。
            """
        )

    def execute(self,goal, output_std, execution_result,human_feedback:str):
        """用 LangChain 整合结果与人工反馈，生成校验和归因报告"""
      
        formatted_feedback_prompt = self.prompt_text_template.format(
            goal=goal, output_std=output_std,
            execution_result=str(execution_result), 
            human_feedback=human_feedback
        )
        
        feedback_report = self.llm([HumanMessage(content=formatted_feedback_prompt)]).content      

        return feedback_report
 
class optimize_stage:
    """
    优化阶段：基于反馈生成改进规则，沉淀经验库
    """
    def __init__(self,llm):
        self.llm = llm
       
        self.prompt_text_template = PromptTemplate(
            input_variables=["feedback_report"],
            template="""
            基于以下反馈报告，生成「可复用的改进规则」，用于下次同类任务（如竞品分析），
            规则需具体（例：规划时需增加「确认数据更新时间」步骤）：
            {feedback_report}
            """
        )        

    def execute(self,feedback_report):
      
        formatted_optim_prompt = self.prompt_text_template.format(feedback_report=feedback_report)
        optimization_rules = self.llm([HumanMessage(content=formatted_optim_prompt)]).content

        self.save_optimization_rules(optimization_rules)
        
        return optimization_rules
    
    def load_optimization_rules(self):
       
        if not os.path.exists("langchain_optim_rules.txt"):
            return ""
      
        with open("langchain_optim_rules.txt", "r", encoding="utf-8") as f:
            return f.read()
       
        
    def save_optimization_rules(self,optimization_rules:str):
        # 保存规则到本地（经验库沉淀）
        with open("langchain_optim_rules.txt", "a", encoding="utf-8") as f:
            f.write(f"\n=== 新规则 ===\n{optimization_rules}\n")

 