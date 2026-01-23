(() => {
  const overlay = document.getElementById('mobile-menu-overlay')
  const openButton = document.querySelector('[data-action="open-menu"]')
  const closeButton = document.querySelector('[data-action="close-menu"]')

  if (!overlay || !openButton) return

  const openMenu = () => {
    overlay.hidden = false
    document.body.style.overflow = 'hidden'
  }

  const closeMenu = () => {
    overlay.hidden = true
    document.body.style.overflow = ''
  }

  openButton.addEventListener('click', openMenu)
  if (closeButton) {
    closeButton.addEventListener('click', closeMenu)
  }

  overlay.addEventListener('click', (event) => {
    if (event.target === overlay) {
      closeMenu()
    }
  })

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && !overlay.hidden) {
      closeMenu()
    }
  })
})()
