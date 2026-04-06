##############################################
# Stage 1: Base image with all tool installs
##############################################
FROM mcr.microsoft.com/devcontainers/javascript-node:24-bullseye AS base

# Install common utils
RUN apt-get update && apt-get install -y \
    apt-utils \
    bash-completion \
    openssh-client \
    gnupg2 \
    dirmngr \
    iproute2 \
    procps \
    lsof \
    htop \
    net-tools \
    psmisc \
    curl \
    tree \
    wget \
    rsync \
    ca-certificates \
    unzip \
    bzip2 \
    xz-utils \
    zip \
    nano \
    vim-tiny \
    less \
    jq \
    lsb-release \
    apt-transport-https \
    dialog \
    libc6 \
    libgcc1 \
    libkrb5-3 \
    libgssapi-krb5-2 \
    libicu[0-9][0-9] \
    liblttng-ust[0-9] \
    libstdc++6 \
    zlib1g \
    locales \
    sudo \
    ncdu \
    man-db \
    strace \
    manpages \
    manpages-dev \
    init-system-helpers \
    build-essential \
    procps \
    file \
    curl \
    git

# Upgrade packages and remove unused dependencies
RUN apt-get -y upgrade --no-install-recommends && apt-get autoremove -y


# Install Github CLI
RUN (type -p wget >/dev/null || (sudo apt update && sudo apt install wget -y)) \
    && sudo mkdir -p -m 755 /etc/apt/keyrings \
    && out=$(mktemp) && wget -nv -O$out https://cli.github.com/packages/githubcli-archive-keyring.gpg \
    && cat $out | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null \
    && sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
    && sudo mkdir -p -m 755 /etc/apt/sources.list.d \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && sudo apt update \
    && sudo apt install gh -y

# Install Golang
RUN curl -fsSL https://go.dev/dl/go1.26.1.linux-amd64.tar.gz | tar -C /usr/local -xz
ENV PATH="/usr/local/go/bin:/root/go/bin:${PATH}"

# Install Codemap
RUN git clone --depth 1 https://github.com/JordanCoin/codemap.git /tmp/codemap \
    && cd /tmp/codemap && /usr/local/go/bin/go build -o /usr/local/bin/codemap . \
    && rm -rf /tmp/codemap

##############################################
# Stage 2: Install non-root tools
##############################################
FROM base AS tools

USER node

# Install Claude Code
RUN curl -fsSL https://claude.ai/install.sh | bash
# Need for claude code to work properly
ENV PATH="/home/node/.local/bin:${PATH}"

RUN NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

ENV PATH="/home/linuxbrew/.linuxbrew/bin:/home/linuxbrew/.linuxbrew/sbin:${PATH}"

# Install TypeScript LSP
RUN npm install -g typescript-language-server typescript rust-just

##############################################
# Stage 3: Prepare scripts
##############################################
FROM tools AS scripts

USER root

COPY configure-claude.sh statusline.sh install-mcps.sh /opt/devcontainer/
RUN chmod +x /opt/devcontainer/*.sh

##############################################
# Stage 4: Configure Claude Code
##############################################

FROM scripts

USER node

ENV DOCKER_MCP_IN_CONTAINER=1

RUN /opt/devcontainer/configure-claude.sh
