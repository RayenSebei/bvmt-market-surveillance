async (page) => {
  const cases = []
  for (const [viewportWidth, viewportHeight] of [[1280, 720], [1920, 1080], [390, 844]]) {
    await page.setViewportSize({ width: viewportWidth, height: viewportHeight })
    for (const view of ['overview', 'feed', 'watchlist']) {
      for (const scrolled of [false, true]) {
        await page.goto(`http://127.0.0.1:5000/terminal?view=${view}`, {
          waitUntil: 'networkidle',
        })
        if (scrolled) {
          await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight / 2))
        }
        await page.getByRole('button', { name: /Inspect/i }).first().click()
        const dialog = page.locator('[role="dialog"]').last()
        await dialog.waitFor()
        await page.waitForTimeout(300)
        const box = await dialog.evaluate((element) => {
          const panel = element.getBoundingClientRect()
          const header = element.querySelector('.v2-inspector-header').getBoundingClientRect()
          const style = getComputedStyle(element)
          return {
            left: panel.left,
            top: panel.top,
            right: panel.right,
            bottom: panel.bottom,
            headerTop: header.top,
            headerBottom: header.bottom,
            transform: style.transform,
            translate: style.translate,
          }
        })
        const inside =
          box.left >= -0.5 &&
          box.top >= -0.5 &&
          box.right <= viewportWidth + 0.5 &&
          box.bottom <= viewportHeight + 0.5 &&
          box.headerTop >= -0.5 &&
          box.headerBottom <= viewportHeight &&
          box.transform === 'none' &&
          box.translate === 'none'
        if (!inside) throw new Error(JSON.stringify({ viewportWidth, viewportHeight, view, scrolled, box }))
        cases.push({ viewportWidth, viewportHeight, view, scrolled, ...box })
      }
    }
  }
  return { passed: cases.length, cases }
}
