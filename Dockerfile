FROM buildpack-deps:buster

RUN useradd -ms /bin/bash learning_hub
WORKDIR /home/learning_hub

# ensure local python is preferred over distribution python
ENV PATH /usr/local/bin:$PATH

# http://bugs.python.org/issue19846
# > At the moment, setting "LANG=C" on a Linux system *fundamentally breaks Python 3*, and that's not OK.
ENV LANG C.UTF-8

# extra dependencies (over what buildpack-deps already includes)
RUN apt-get update && apt-get install -y --no-install-recommends \
		libbluetooth-dev \
		tk-dev \
		uuid-dev \
	&& rm -rf /var/lib/apt/lists/*

ENV GPG_KEY E3FF2839C048B25C084DEBE9B26995E310250568
ENV PYTHON_VERSION 3.8.11

RUN set -ex \
	\
	&& wget -O python.tar.xz "https://www.python.org/ftp/python/${PYTHON_VERSION%%[a-z]*}/Python-$PYTHON_VERSION.tar.xz" \
	&& wget -O python.tar.xz.asc "https://www.python.org/ftp/python/${PYTHON_VERSION%%[a-z]*}/Python-$PYTHON_VERSION.tar.xz.asc" \
	&& export GNUPGHOME="$(mktemp -d)" \
	&& gpg --batch --keyserver hkps://keys.openpgp.org --recv-keys "$GPG_KEY" \
	&& gpg --batch --verify python.tar.xz.asc python.tar.xz \
	&& { command -v gpgconf > /dev/null && gpgconf --kill all || :; } \
	&& rm -rf "$GNUPGHOME" python.tar.xz.asc \
	&& mkdir -p /usr/src/python \
	&& tar -xJC /usr/src/python --strip-components=1 -f python.tar.xz \
	&& rm python.tar.xz \
	\
	&& cd /usr/src/python \
	&& gnuArch="$(dpkg-architecture --query DEB_BUILD_GNU_TYPE)" \
	&& ./configure \
		--build="$gnuArch" \
		--enable-loadable-sqlite-extensions \
		--enable-optimizations \
		--enable-option-checking=fatal \
		--enable-shared \
		--with-system-expat \
		--with-system-ffi \
		--without-ensurepip \
	&& make -j "$(nproc)" \
	&& make install \
	&& rm -rf /usr/src/python \
	\
	&& find /usr/local -depth \
		\( \
			\( -type d -a \( -name test -o -name tests -o -name idle_test \) \) \
			-o \( -type f -a \( -name '*.pyc' -o -name '*.pyo' -o -name '*.a' \) \) \
			-o \( -type f -a -name 'wininst-*.exe' \) \
		\) -exec rm -rf '{}' + \
	\
	&& ldconfig \
	\
	&& python3 --version

# make some useful symlinks that are expected to exist
RUN cd /usr/local/bin \
	&& ln -s idle3 idle \
	&& ln -s pydoc3 pydoc \
	&& ln -s python3 python \
	&& ln -s python3-config python-config

# if this is called "PIP_VERSION", pip explodes with "ValueError: invalid truth value '<VERSION>'"
ENV PYTHON_PIP_VERSION 21.1.3
# https://github.com/pypa/get-pip
ENV PYTHON_GET_PIP_URL https://github.com/pypa/get-pip/raw/a1675ab6c2bd898ed82b1f58c486097f763c74a9/public/get-pip.py
ENV PYTHON_GET_PIP_SHA256 6665659241292b2147b58922b9ffe11dda66b39d52d8a6f3aa310bc1d60ea6f7

RUN set -ex; \
	\
	wget -O get-pip.py "$PYTHON_GET_PIP_URL"; \
	echo "$PYTHON_GET_PIP_SHA256 *get-pip.py" | sha256sum --check --strict -; \
	\
	python get-pip.py \
		--disable-pip-version-check \
		--no-cache-dir \
		"pip==$PYTHON_PIP_VERSION" \
	; \
	pip --version; \
	\
	find /usr/local -depth \
		\( \
			\( -type d -a \( -name test -o -name tests -o -name idle_test \) \) \
			-o \
			\( -type f -a \( -name '*.pyc' -o -name '*.pyo' \) \) \
		\) -exec rm -rf '{}' +; \
	rm -f get-pip.py

CMD ["python3"]

COPY requirements.txt requirements.txt
COPY Fonts Fonts
RUN python -m venv venv
#RUN pip freeze > requirements.txt
RUN apt-get update && apt-get install -y python3-dev \
&& apt-get install -y libffi-dev \
&& apt-get install -y openssl \
&& apt-get install -y python3-opencv \
&& apt-get install -y libssl-dev
RUN apt-get update && apt-get install -y postgresql \
&& apt-get install postgresql-contrib \
&& apt-get install -y gcc \
&& apt-get install -y musl-dev

RUN venv/bin/python -m pip install --upgrade pip
RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install gunicorn

COPY app app
# COPY migrations migrations
COPY main.py config.py boot.sh ./
RUN chmod +x boot.sh

ENV FLASK_APP main.py
ENV SECRET_KEY=237138863277163537437277146029470316302
ENV DATABASE_URL=postgresql+psycopg2://lutfi:root@localhost:5432/learning_hub_db
ENV VAPID_PUBLIC_KEY=BASteBa25XYp1gv9-s__Rqx70jaBncTZJ4E7WLfpXCSLkRGoNE4bCpH_0RVGX0YMptzvEjuZQnLg_eYdKuNT4uA
ENV VAPID_PRIVATE_KEY=eLF4r4s6_-sdBbCeUilGGZKBC6Jh04eY09b7029t7qs
ENV VAPID_CLAIM_EMAIL=lutfi.rabago@g42.ai
ENV MAIL_SERVER=172.18.228.12
ENV MAIL_DEFAULT_SENDER=svc_biogenix@g42.ai
ENV MAIL_PORT=587
ENV MAIL_USE_TLS=1
ENV MAIL_USERNAME=svc_biogenix
ENV MAIL_PASSWORD=QA$(%p#bNw9tpds]xx_8QC

RUN chown -R learning_hub:learning_hub ./
USER learning_hub

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]

#FROM python:3.8-alpine
#
#RUN adduser -D lutfi
#
#WORKDIR /home/learning_hub
#
#COPY requirements.txt requirements.txt
#RUN python -m venv venv
##RUN pip freeze > requirements.txt
#RUN apk update && apk add alpine-sdk python3-dev libffi-dev openssl-dev
#RUN apk add --no-cache postgresql-libs && \
#    apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev
#RUN venv/bin/python -m pip install --upgrade pip
#RUN venv/bin/pip install -r requirements.txt
#RUN venv/bin/pip install gunicorn
#
#COPY app app
## COPY migrations migrations
#COPY main.py config.py boot.sh ./
#RUN chmod +x boot.sh
#
#ENV FLASK_APP main.py
#
#RUN chown -R lutfi:lutfi ./
#USER lutfi
#
#EXPOSE 5000
#ENTRYPOINT ["./boot.sh"]