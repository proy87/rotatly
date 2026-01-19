window.hide_element = (el)->
  display = window.getComputedStyle(el, null).display
  if display != 'none'
    el.setAttribute('data-display', display)
  el.style.display = 'none'

window.show_element = (el)->
  display = window.getComputedStyle(el, null).display
  if display == 'none'
    el.style.display = el.getAttribute('data-display') or 'block'

window.get_request = (url, data)->
  params = []
  for k, v of data
    params.push("#{k}=#{v}")
  await fetch(url + '?' + params.join('&'))