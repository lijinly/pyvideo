from enum import Enum
from dataclasses import dataclass
from typing import Union


@dataclass
class ErrorInfo:
    """错误信息类"""
    code: int
    message: str


class ErrorCode(Enum):
    """错误码枚举"""
    # 通用错误 (1000-1099)
    SUCCESS = ErrorInfo(1000, "Success")
    VALIDATION_ERROR = ErrorInfo(1001, "数据验证失败")
    INTERNAL_ERROR = ErrorInfo(1002, "服务异常，请稍后重试")
    
    # 认证错误 (2000-2099)
    AUTHENTICATION_FAILED = ErrorInfo(2001, "认证失败")
    TOKEN_EXPIRED = ErrorInfo(2002, "认证失败")
    # TOKEN_INVALID = ErrorInfo(2003, "认证失败")
    TOKEN_REVOKED = ErrorInfo(2004, "认证失败")
    LOGOUT_FAILED = ErrorInfo(2005, "登出失败")
    
    # 用户错误 (3000-3099)
    USER_NOT_FOUND = ErrorInfo(3001, "用户不存在")
    USER_ALREADY_EXISTS = ErrorInfo(3002, "用户已存在")
    INVALID_CREDENTIALS = ErrorInfo(3003, "用户名或密码错误")
    
    # 资源错误 (4000-4099)
    ASSET_NOT_FOUND = ErrorInfo(4001, "资源不存在")


def make_response(error_code: ErrorCode, data: Union[dict, list, str, None] = None, sub_message: str = None) -> dict:
    """
    创建统一响应格式
    
    Args:
        error_code: 错误码枚举值
        data: 响应数据
        sub_message: 子消息，通常用于详细错误信息
        
    Returns:
        dict: 统一响应格式
    """
    response = {
        "code": error_code.value.code,
        "message": error_code.value.message
    }
    
    if sub_message is not None:
        response["sub_message"] = sub_message
    
    if data is not None:
        response["data"] = data
        
    return response