FROM python:3.7
LABEL ababa831 "flvonlineconverter@gmail.com"

SHELL ["/bin/bash", "-c"]

WORKDIR /home

# 必要なpackageのインストール．
# editor関係は任意で追加可
RUN apt update --fix-missing
# Ref: https://qiita.com/yagince/items/deba267f789604643bab
ENV DEBIAN_FRONTEND=noninteractive
RUN apt install -y  \
    tzdata \
    systemd \
    locales \
    iproute2 \
    curl \
    wget \
    git \
    sudo \
    unzip \
    nano
RUN rm -rf /root/.cache

# 地域，言語等の設定
RUN locale-gen ja_JP.UTF-8
ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:ja
ENV LC_ALL ja_JP.UTF-8

# TimeZoneをJSTへ
RUN ln -sf /usr/share/zoneinfo/Asia/Tokyo /etc/localtime

# 定義したエントリポイントをホストOSからコピー
COPY entrypoint.sh /home
COPY main.py /home

# poetry
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | /usr/local/bin/python -
ENV PATH $PATH:/root/.poetry/bin
RUN poetry config virtualenvs.in-project false
COPY poetry.lock /home
COPY pyproject.toml /home
RUN poetry install

ENTRYPOINT [ "./entrypoint.sh" ]