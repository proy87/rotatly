window.hide_element = (el)->
  display = window.getComputedStyle(el, null).display
  if display != 'none'
    el.setAttribute('data-display', display)
  el.style.display = 'none'

window.show_element = (el)->
  display = window.getComputedStyle(el, null).display
  if display == 'none'
    el.style.display = el.getAttribute('data-display') or 'block'

get_cookie = (name) ->
  if document.cookie and document.cookie != ''
    cookies = document.cookie.split(';')
    for i in [0...cookies.length]
      cookie = cookies[i].trim()
      if cookie.substring(0, name.length + 1) == (name + '=')
        return decodeURIComponent(cookie.substring(name.length + 1))

window.send_request = (url, data, method = 'POST', callback = null)->
  params = []
  for k, v of data
    params.push("#{k}=#{v}")
  params_str = params.join('&')
  body = null
  headers = null
  if method == 'POST'
    headers = {
      'Content-Type': 'application/x-www-form-urlencoded',
      'X-CSRFToken': get_cookie('csrftoken')
    }
    body = params_str
  else
    url += "?#{params_str}"
  await fetch(url,
    method: method,
    headers: headers,
    body: body,
  ).then((r)->
    if r.ok
      return r.json()
  ).then((data)->
    if callback
      callback(data)
  )