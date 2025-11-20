FROM mcr.microsoft.com/azure-functions/python:4-python3.11

# 作業ディレクトリを設定
ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true

# 依存パッケージのインストール
COPY requirements.txt /
RUN pip install --no-cache-dir -r /requirements.txt

# 関数コードをコピー
COPY . /home/site/wwwroot
