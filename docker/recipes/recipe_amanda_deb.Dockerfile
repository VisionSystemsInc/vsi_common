FROM debian:8

SHELL ["bash", "-xveuc"]

ONBUILD ARG AMANDA_VERSION=tags/community_3_4_5
ONBUILD RUN set -euxv; \
            useradd amandabackup -u 63998 -g disk; \
            build_deps="curl ca-certificates build-essential automake autoconf libtool \
                        libglib2.0-dev fakeroot debhelper dump flex libssl-dev \
                        libncurses5-dev smbclient mtx byacc swig \
                        libcurl4-openssl-dev bsd-mailx libreadline-dev gnuplot-nox"; \
            # autogen pkg-config autoconf-archive autopoint"; \
            apt-get update; \
            DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends ${build_deps}; \
            #curl -LO https://github.com/zmanda/amanda/archive/${AMANDA_VERSION}/amanda.tar.gz; \
            curl -LO https://github.com/andyneff/amanda/archive/${AMANDA_VERSION}/amanda.tar.gz; \
            tar zxf amanda.tar.gz; \
            cd amanda-${AMANDA_VERSION//\//-}; \
            ./autogen; \
            #sed -i 's|--with-bsdtcp-security.*|&\n--with-low-tcpportrange=880,882 \\\n--with-tcpportrange=11070,11071 \\\n--with-udpportrange=883,885 \\|' ./packaging/deb/rules; \
            packaging/deb/buildpkg; \
            mv *.deb ../; \
            DEBIAN_FRONTEND=noninteractive apt-get purge --auto-remove -y ${build_deps}; \
            cd / ; \
            rm -r /amanda.tar.gz /amanda-${AMANDA_VERSION//\//-}