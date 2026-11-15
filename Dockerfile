# Slugs (GR(1) synthesis) is built from source in a throw-away stage
FROM debian:stable-slim AS slugs
ARG SLUGS_COMMIT=ac09bf652d4ff47a7018d6a41627af73a67a049c
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl g++ make libboost-dev \
    && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL https://github.com/VerifiableRobotics/slugs/archive/${SLUGS_COMMIT}.tar.gz \
    | tar -xz -C /opt && mv /opt/slugs-${SLUGS_COMMIT} /opt/slugs \
    && make -C /opt/slugs/src -j"$(nproc)"


FROM debian:stable-slim

ARG NUSMV_VERSION=2.7.1

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl xz-utils make graphviz python3 python3-venv \
        libxml2 libedit2 \
    && rm -rf /var/lib/apt/lists/*

# Spot (ltlsynt, ltl2tgba, autfilt, ...) from the upstream Debian repository
RUN curl -fsSL https://www.lrde.epita.fr/repo/debian.gpg -o /etc/apt/trusted.gpg.d/lrde.gpg \
    && echo 'deb https://www.lrde.epita.fr/repo/debian/ stable/' > /etc/apt/sources.list.d/lrde.list \
    && apt-get update && apt-get install -y --no-install-recommends spot \
    && rm -rf /var/lib/apt/lists/*

# NuSMV model checker (prebuilt binary)
RUN curl -fsSL https://nusmv.fbk.eu/distrib/${NUSMV_VERSION}/NuSMV-${NUSMV_VERSION}-linux64.tar.xz \
    | tar -xJ -C /opt \
    && ln -s /opt/NuSMV-${NUSMV_VERSION}-linux64/bin/NuSMV /usr/local/bin/NuSMV \
    # the binary wants libedit.so.0 (Red Hat name); Debian ships the same library as .so.2
    && ln -s libedit.so.2 /usr/lib/x86_64-linux-gnu/libedit.so.0

# Slugs binary and its structured-spec compiler
COPY --from=slugs /opt/slugs/src/slugs /usr/local/bin/slugs
COPY --from=slugs /opt/slugs/tools/StructuredSlugsParser /opt/slugs-compiler
COPY --from=slugs /opt/slugs/LICENSE.txt /opt/slugs-compiler/LICENSE.txt

# Typst, for the report
ARG TYPST_VERSION=0.15.1
RUN curl -fsSL https://github.com/typst/typst/releases/download/v${TYPST_VERSION}/typst-x86_64-unknown-linux-musl.tar.xz \
    | tar -xJ -C /opt \
    && ln -s /opt/typst-x86_64-unknown-linux-musl/typst /usr/local/bin/typst

# Python packages in a venv on PATH
COPY requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt
ENV PATH=/opt/venv/bin:$PATH \
    HOME=/tmp \
    MPLBACKEND=Agg

WORKDIR /work
CMD ["bash"]
