try:
    import kaleido
    from choreographer.browsers.chromium import ChromeNotFoundError

    import logging

    log = logging.getLogger("red.vex-utils")

    async def kaleido_setup() -> bool:
        """
        Install Kaleido's rendering engine (Chromium) if it's not already installed.
        """
        try:
            kaleido.Kaleido()
            log.info("Kaleido rendering engine (Chromium) found")
        except ChromeNotFoundError:
            log.info("Kaleido rendering engine (Chromium) not found, downloading now")
            location = await kaleido.get_chrome()
            log.info("Kaleido rendering engine backend is ready to use, at %s", location)

        return True

except ImportError:

    def kaleido_setup() -> None:
        raise ImportError("Kaleido is not installed so this util is not required.")
