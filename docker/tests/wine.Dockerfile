FROM andyneff/wine_msys64:ubuntu_14.04

ADD setup_entrypoint.bsh /
RUN chmod 755 /setup_entrypoint.bsh
ENTRYPOINT ["/wine_entrypoint.bsh", "--add", "/setup_entrypoint.bsh"]
