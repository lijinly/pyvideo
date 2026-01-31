# 生成初始requirements.txt
pipreqs . --force --encoding=utf8 --ignore=.venv --ignore=.asset_space --ignore=.logs --ignore=.work_space  2>&1 | Out-Null

# 添加gunicorn（如果存在则先删除）
$content = Get-Content requirements.txt -Raw

# 移除所有现有 gunicorn 条目
$updatedContent = $content -replace '(?m)^gunicorn[^\n]*\r?\n', ''
$updatedContent += "gunicorn==23.0.0`r`n"

$updatedContent = $updatedContent -replace '(?m)^scikit-learn[^\n]*\r?\n', ''
$updatedContent += "scikit-learn==1.6.1`r`n"

# 会提前安装

$updatedContent = $updatedContent -replace '(?m)^torch==[^\n]*\r?\n', ''
$updatedContent = $updatedContent -replace '(?m)^torchaudio[^\n]*\r?\n', ''
$updatedContent = $updatedContent -replace '(?m)^torchvision[^\n]*\r?\n', ''
$updatedContent = $updatedContent -replace '(?m)^transformers[^\n]*\r?\n', ''
# 保存更新后的内容
Set-Content -Path requirements.txt -Value $updatedContent -Encoding utf8
 

# # 提取所有包名（包括新添加的gunicorn）
$packages = (Get-Content requirements.txt | ForEach-Object { $_.Split('=')[0].Trim() } | Where-Object { $_ }) -join ','

# # 导出所有依赖
pipdeptree --packages $packages --freeze > requirements.txt

 