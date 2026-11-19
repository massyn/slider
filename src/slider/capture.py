"""Screenshot every moment of a rendered deck in headless Chromium.

Relies on the theme contract: slides are `.slide` elements, revealable items are `.step`,
narration is in `data-voice`, and `window.slider.show(slide, step)` sets the view.
"""

import logging
from dataclasses import dataclass
from pathlib import Path

from playwright.async_api import async_playwright

from slider.deck import DeckError
from slider.timeline import Moment, moments

logger = logging.getLogger(__name__)

# Stills are taken between transitions, so switch them off to capture the settled state.
_NO_MOTION = "*, *::before, *::after { transition: none !important; animation: none !important; }"

_STRUCTURE = """() => [...document.querySelectorAll('.slide')].map(slide => ({
    voice: slide.dataset.voice || '',
    steps: [...slide.querySelectorAll('.step')].map(step => step.dataset.voice || ''),
}))"""


@dataclass(frozen=True)
class Still:
    moment: Moment
    path: Path


async def film(page_file: Path, folder: Path, width: int, height: int) -> list[Still]:
    """Open the deck page and save one PNG per moment into `folder`."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page(viewport={"width": width, "height": height})
            await page.goto(page_file.resolve().as_uri())
            await page.add_style_tag(content=_NO_MOTION)
            if not await page.evaluate(
                "() => typeof window.slider?.show === 'function'"
            ):
                raise DeckError("Theme does not expose window.slider.show(slide, step)")

            stills = []
            for moment in moments(await page.evaluate(_STRUCTURE)):
                await page.evaluate(
                    "([slide, step]) => window.slider.show(slide, step)",
                    [moment.slide, moment.step],
                )
                path = folder / f"{len(stills):04d}.png"
                await page.screenshot(path=str(path))
                stills.append(Still(moment, path))
        finally:
            await browser.close()
    logger.info("Captured %d moments", len(stills))
    return stills
