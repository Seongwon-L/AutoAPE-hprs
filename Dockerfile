FROM registry.seculayer.com:31500/ape/python-base:py3.7 as builder
ARG app="/opt/app"

RUN mkdir -p $app
WORKDIR $app

COPY ./requirements.txt ./requirements.txt
RUN pip3.7 install -r ./requirements.txt -t $app/lib

COPY ./hprs ./hprs
COPY ./setup.py ./setup.py

RUN pip3.7 install wheel
RUN python3.7 setup.py bdist_wheel

FROM registry.seculayer.com:31500/ape/python-base:py3.7 as app
ARG app="/opt/app"
ENV LANG=en_US.UTF-8 LANGUAGE=en_US:en LC_ALL=en_US.UTF-8

RUN mkdir -p /eyeCloudAI/app/ape/hprs
WORKDIR /eyeCloudAI/app/ape/hprs

COPY ./hprs.sh /eyeCloudAI/app/ape/hprs

COPY --from=builder "$app/lib" /eyeCloudAI/app/ape/hprs/lib

COPY --from=builder "$app/dist/hprs-1.0.0-py3-none-any.whl" \
        /eyeCloudAI/app/ape/hprs/hprs-1.0.0-py3-none-any.whl

RUN pip3.7 install /eyeCloudAI/app/ape/hprs/hprs-1.0.0-py3-none-any.whl --no-dependencies  \
    -t /eyeCloudAI/app/ape/hprs \
    && rm /eyeCloudAI/app/ape/hprs/hprs-1.0.0-py3-none-any.whl

RUN groupadd -g 1000 aiuser
RUN useradd -r -u 1000 -g aiuser aiuser
RUN chown -R aiuser:aiuser /eyeCloudAI
USER aiuser

CMD []