FROM python:3.11.3-slim-buster

RUN apt-get update
RUN apt install -y locales && localedef -f UTF-8 -i ja_JP ja_JP.UTF-8
ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:ja
ENV LC_ALL ja_JP.UTF-8
ENV TZ JST-9

RUN apt-get -y upgrade && \
    apt-get install -y fonts-noto-cjk

RUN pip install --upgrade pip
RUN pip install matplotlib \
                streamlit==1.22.0 \
                fastf1

RUN mkdir -p /root/.config/matplotlib
ADD matplotlibrc /root/.config/matplotlib/matplotlibrc

WORKDIR /app

ENTRYPOINT ["streamlit"]
CMD ["run"]
