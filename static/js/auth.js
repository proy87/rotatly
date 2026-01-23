(() => {
  const apiBase = ''

  const setMessage = (container, type, text) => {
    if (!container) return
    if (!text) {
      container.hidden = true
      container.textContent = ''
      container.classList.remove('form-message--error', 'form-message--success')
      return
    }
    container.hidden = false
    container.textContent = text
    container.classList.remove('form-message--error', 'form-message--success')
    if (type) {
      container.classList.add(`form-message--${type}`)
    }
  }

  const setButtonLoading = (button, loading, loadingText) => {
    if (!button) return
    const baseText = button.getAttribute('data-base-text') || button.textContent
    if (!button.getAttribute('data-base-text')) {
      button.setAttribute('data-base-text', baseText)
    }
    if (loading) {
      button.disabled = true
      if (loadingText) {
        button.textContent = loadingText
      }
    } else {
      button.disabled = false
      button.textContent = button.getAttribute('data-base-text')
    }
  }

  const postJson = async (url, payload) => {
    const response = await fetch(`${apiBase}${url}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    })
    const data = await response.json().catch(() => ({}))
    return { response, data }
  }

  const initPasswordToggles = () => {
    document.querySelectorAll('[data-toggle-password]').forEach((button) => {
      const targetSelector = button.getAttribute('data-target')
      const target = targetSelector ? document.querySelector(targetSelector) : null
      if (!target) return
      button.addEventListener('click', () => {
        const isVisible = target.getAttribute('type') === 'text'
        target.setAttribute('type', isVisible ? 'password' : 'text')
        const icon = button.querySelector('.password-toggle-icon')
        if (icon) {
          icon.classList.toggle('fa-eye', isVisible)
          icon.classList.toggle('fa-eye-slash', !isVisible)
        }
        button.setAttribute('aria-label', isVisible ? 'Show password' : 'Hide password')
      })
    })
  }

  const initAuthForms = () => {
    document.querySelectorAll('[data-auth-form]').forEach((form) => {
      const formType = form.getAttribute('data-auth-form')
      const message = form.querySelector('[data-form-message]') ||
        form.parentElement?.querySelector('[data-form-message]')
      const submitButton = form.querySelector('button[type="submit"]')

      form.addEventListener('submit', async (event) => {
        event.preventDefault()
        setMessage(message, null, '')

        if (formType === 'login') {
          const email = form.querySelector('[name="email"]')?.value.trim()
          const password = form.querySelector('[name="password"]')?.value
          if (!email || !password) {
            setMessage(message, 'error', 'Enter your email and password.')
            return
          }
          setButtonLoading(submitButton, true, 'Logging in...')
          try {
            const { response, data } = await postJson('/api/auth/login/', {
              email,
              password,
            })
            if (!response.ok) {
              setMessage(message, 'error', data.error || 'Login failed. Please try again.')
              return
            }
            setMessage(message, 'success', 'Welcome back!')
            window.location.href = '/'
          } catch {
            setMessage(message, 'error', 'Unable to reach the server. Try again soon.')
          } finally {
            setButtonLoading(submitButton, false)
          }
        }

        if (formType === 'signup') {
          const username = form.querySelector('[name="username"]')?.value.trim()
          const email = form.querySelector('[name="email"]')?.value.trim()
          const password = form.querySelector('[name="password"]')?.value
          const confirmPassword = form.querySelector('[name="confirm_password"]')?.value
          if (!username || !email || !password || !confirmPassword) {
            setMessage(message, 'error', 'Fill in all fields to create your account.')
            return
          }
          if (password !== confirmPassword) {
            setMessage(message, 'error', 'Passwords do not match.')
            return
          }
          setButtonLoading(submitButton, true, 'Creating...')
          try {
            const { response, data } = await postJson('/api/auth/signup/', {
              username,
              email,
              password,
              confirm_password: confirmPassword,
            })
            if (!response.ok) {
              setMessage(message, 'error', data.error || 'Sign up failed. Please try again.')
              return
            }
            setMessage(message, 'success', 'Account created! You can log in now.')
          } catch {
            setMessage(message, 'error', 'Unable to reach the server. Try again soon.')
          } finally {
            setButtonLoading(submitButton, false)
          }
        }

        if (formType === 'reset') {
          const email = form.querySelector('[name="email"]')?.value.trim()
          if (!email) {
            setMessage(message, 'error', 'Enter your email address to continue.')
            return
          }
          setButtonLoading(submitButton, true, 'Sending...')
          try {
            const { response, data } = await postJson('/api/auth/reset-password/', { email })
            if (!response.ok) {
              setMessage(message, 'error', data.error || 'Unable to send reset email. Try again.')
              return
            }
            localStorage.setItem('resetEmail', email)
            window.location.href = '/reset-email/'
          } catch {
            setMessage(message, 'error', 'Unable to reach the server. Try again soon.')
          } finally {
            setButtonLoading(submitButton, false)
          }
        }

        if (formType === 'new-password') {
          const params = new URLSearchParams(window.location.search)
          const uid = params.get('uid') || ''
          const token = params.get('token') || ''
          const password = form.querySelector('[name="password"]')?.value
          const confirmPassword = form.querySelector('[name="confirm_password"]')?.value
          if (!uid || !token) {
            setMessage(message, 'error', 'Invalid or expired reset link.')
            return
          }
          if (!password || !confirmPassword) {
            setMessage(message, 'error', 'Enter and confirm your new password.')
            return
          }
          if (password !== confirmPassword) {
            setMessage(message, 'error', 'Passwords do not match.')
            return
          }
          setButtonLoading(submitButton, true, 'Resetting...')
          try {
            const { response, data } = await postJson('/api/auth/reset-password/confirm/', {
              uid,
              token,
              password,
              confirm_password: confirmPassword,
            })
            if (!response.ok) {
              setMessage(message, 'error', data.error || 'Unable to reset password. Try again.')
              return
            }
            const section = form.closest('[data-new-password]')
            const successPanel = section?.querySelector('[data-success-panel]')
            const formPanel = section?.querySelector('[data-form-panel]')
            if (formPanel) formPanel.hidden = true
            if (successPanel) successPanel.hidden = false
            setMessage(message, null, '')
          } catch {
            setMessage(message, 'error', 'Unable to reach the server. Try again soon.')
          } finally {
            setButtonLoading(submitButton, false)
          }
        }
      })
    })
  }

  const initResetEmail = () => {
    const section = document.querySelector('[data-reset-email]')
    if (!section) return
    const resendButton = section.querySelector('[data-resend-button]')
    const timerLabel = section.querySelector('[data-resend-timer]')
    const message = section.querySelector('[data-form-message]')
    const email = localStorage.getItem('resetEmail') || ''
    let secondsLeft = 60

    const updateTimer = () => {
      if (!timerLabel) return
      timerLabel.textContent = `${secondsLeft}s`
    }

    const tick = () => {
      if (secondsLeft <= 0) {
        secondsLeft = 0
        if (resendButton) resendButton.disabled = !email
        updateTimer()
        return
      }
      secondsLeft -= 1
      updateTimer()
      if (secondsLeft > 0) {
        window.setTimeout(tick, 1000)
      } else if (resendButton) {
        resendButton.disabled = !email
      }
    }

    updateTimer()
    if (resendButton) resendButton.disabled = true
    window.setTimeout(tick, 1000)

    if (resendButton) {
      resendButton.addEventListener('click', async () => {
        if (!email || secondsLeft > 0) return
        setMessage(message, null, '')
        setButtonLoading(resendButton, true, 'Sending...')
        try {
          const { response, data } = await postJson('/api/auth/reset-password/', { email })
          if (!response.ok) {
            setMessage(message, 'error', data.error || 'Unable to resend email. Try again.')
            return
          }
          setMessage(message, 'success', 'Reset email sent.')
          secondsLeft = 60
          resendButton.disabled = true
          updateTimer()
          window.setTimeout(tick, 1000)
        } catch {
          setMessage(message, 'error', 'Unable to reach the server. Try again soon.')
        } finally {
          setButtonLoading(resendButton, false)
        }
      })
    }
  }

  initPasswordToggles()
  initAuthForms()
  initResetEmail()
})()
