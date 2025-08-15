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
        except AttributeError:
            log.error(
                "An old version of Kaleido is installed, it should already have been updated, "
                "please restart your bot to ensure the latest version is used. If this doesn't "
                "work, please contact Vexed for support in the cog support server "
                "https://discord.gg/GD43Nb9H86"
            )
            return False
        return True

except ImportError:

    def kaleido_setup() -> None:
        raise ImportError("Kaleido is not installed so this util is not required.")
