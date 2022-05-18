FROM python:3

ENV DEBIAN_FRONTEND=noninteractive

# UID and GID as obtained from bacssaas user on ROME id -u, id -g
ARG USER_NAME

# ammend user librarires
ENV LD_LIBRARY_PATH="/usr/local/lib:${LD_LIBRARY_PATH}"

# generic packages
RUN apt-get update && apt-get install -y keyboard-configuration python3-venv python3-pyqt5

# install python depencies
ADD /include ./orchestrator
RUN pip install --no-cache-dir -r ./orchestrator/requirements.txt

# create user working directory

RUN useradd -d /home/${USER_NAME} -m ${USER_NAME} && \
    chown -R ${USER_NAME} /home/${USER_NAME} && \
    adduser ${USER_NAME} sudo && \
    echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

USER $USER_NAME
ENV HOME /home/$USER_NAME
ARG workdir=/home/$USER_NAME

WORKDIR $workdir

#CMD [ "python", "/orchestrator/main.py" ]

RUN echo -e '\n \e[1;34mInstallation complete\033[0m \n'