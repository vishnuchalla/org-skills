FROM golang:1.25-bookworm

# Install Python 3 and development tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-dev \
    python3-venv \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install common Python tools
RUN pip3 install --no-cache-dir --break-system-packages \
    pytest \
    requests \
    pyyaml

# Install GitHub CLI
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
    | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
    | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update && apt-get install -y gh \
    && rm -rf /var/lib/apt/lists/*

# Create claude user with root group for OpenShift compatibility
RUN useradd -m -u 1000 -g 0 -s /bin/bash claude

# Copy org-skills repository to /opt/org-skills
COPY . /opt/org-skills
RUN chown -R claude:root /opt/org-skills

# Create Claude configuration directory and copy settings
#   Note: We pre-configure known_marketplaces.json because extraKnownMarketplaces
#   doesn't seem to work in non-interactive mode.
RUN mkdir -p /home/claude/.claude/plugins
COPY images/claude-settings.json /home/claude/.claude/settings.json
COPY images/known_marketplaces.json /home/claude/.claude/plugins/known_marketplaces.json
RUN chown -R claude:root /home/claude

# Create workspace directory
RUN mkdir -p /workspace && chown -R claude:root /workspace
WORKDIR /workspace

# Switch to claude user
USER claude

# Install Claude Code CLI using the official installation script
RUN curl -fsSL https://claude.ai/install.sh | bash

# In CI, OpenShift uses a random UID, but in the root group
RUN chmod -R g+rwx /home/claude && \
    chmod -R g+rwx /opt/org-skills && \
    chmod -R g+rwx /workspace

# Ensure ~/.local/bin is in PATH for the entrypoint
ENV PATH="/home/claude/.local/bin:${PATH}"
ENV CLAUDE_CONFIG_DIR="/home/claude/.claude"

# Set Claude Code as the default command
ENTRYPOINT ["claude"]

# Default to showing help
CMD ["--help"]
