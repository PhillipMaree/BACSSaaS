FROM nvidia/cuda:11.0-base

ENV DEBIAN_FRONTEND=noninteractive

# UID and GID as obtained from bacssaas user on ROME id -u, id -g
ARG USER_NAME

# generic packages
RUN apt-get update && apt-get install --no-install-recommends --no-install-suggests -y \
    sudo \
    curl \
    unzip \
    keyboard-configuration \
    python3-setuptools python3 python3-pip python3-pyqt5 python3.8-venv

# install python depencies
ADD /include ./orchestrator
RUN pip3 install --upgrade pip Pillow --no-cache-dir -r ./orchestrator/requirements.txt

# create user working directory
RUN useradd -d /home/${USER_NAME} -m ${USER_NAME} && \
    chown -R ${USER_NAME} /home/${USER_NAME} && \
    adduser ${USER_NAME} sudo && \
    echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

USER $USER_NAME
ENV HOME /home/$USER_NAME
ARG workdir=/home/$USER_NAME
WORKDIR $workdir

ENV LD_LIBRARY_PATH="/usr/local/lib:${LD_LIBRARY_PATH}"

RUN echo -e '\n \e[1;34mInstallation complete\033[0m \n'