window.hide_element = (el)->
  display = window.getComputedStyle(el, null).display
  if display != 'none'
    el.setAttribute('data-display', display)
  el.style.display = 'none'

window.show_element = (el)->
  display = window.getComputedStyle(el, null).display
  if display == 'none'
    el.style.display = el.getAttribute('data-display') or 'block'

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
      'X-CSRFToken': csrf_token
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