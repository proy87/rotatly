selected_color_icon = null
game_dom = document.querySelector('#game-container')
game_board = game_dom.querySelector('table')
game_grid = game_dom.querySelector('.outline-grid')
outline_dom = document.querySelector('#outline')
outline_board = outline_dom.querySelector('table')

nodes = document.querySelectorAll('.node')

N = outline_board.rows.length
M = outline_board.rows[0].cells.length

color_palette_dom = document.getElementById("color-palette")
board_palette_dom = document.getElementById("board-palette")

for item in color_palette_dom.getElementsByClassName('color-icon')
  item.addEventListener('click', ->
    if selected_color_icon
      selected_color_icon.classList.remove('selected')
      if selected_color_icon == this
        selected_color_icon = null
        return
    this.classList.add('selected')
    selected_color_icon = this
  )

remove_data = (el, palette)->
  color_class = el.getAttribute('data-class')
  if color_class
    el.classList.remove(color_class)
    window.show_element(palette.querySelector(".#{color_class}"))
  el.removeAttribute('data-class')
  el.removeAttribute('data-index')
  el.removeAttribute('data-name')
  span = el.querySelector('span')
  if span
    span.innerHTML = ''

set_data = (target, source, palette)->
  remove_data(target, palette)
  if source
    klass = source.getAttribute('data-class')
    name = source.getAttribute('data-name')
    target.classList.add(klass)
    target.setAttribute('data-class', klass)
    target.setAttribute('data-index', source.getAttribute('data-index'))
    target.setAttribute('data-name', name)
    if name
      target.querySelector('span').innerHTML = name

game_board.querySelectorAll('td').forEach((cell) ->
  cell.addEventListener("click", ->
    remove_data(cell, board_palette_dom)
  )
)

draggable_item_clone = null
create_clone = (source, click_listener = null)->
  clone = source.cloneNode(true)
  clone.style.position = 'absolute'
  clone.style.left = source.offsetLeft + 'px'
  clone.style.top = source.offsetTop + 'px'
  if click_listener
    clone.addEventListener('click', click_listener)
  source.after(clone)
  return clone


interact('.board-item').draggable(
  onstart: (evt)->
    draggable_item_clone = create_clone(evt.target)
  onmove: (evt)->
    el = evt.target

    x = (parseFloat(el.dataset.x) || 0) + evt.dx
    y = (parseFloat(el.dataset.y) || 0) + evt.dy
    el.style.transform = "translate(#{x}px, #{y}px)"
    el.dataset.x = x
    el.dataset.y = y
  onend: (evt)->
    el = evt.target
    el.style.transform = ''
    el.removeAttribute('data-x')
    el.removeAttribute('data-y')
    draggable_item_clone.remove()
    draggable_item_clone = null
).styleCursor(false)

interact('#game-container td').dropzone(
  accept: '.board-item'
  overlap: 0.75,
  ondrop: (evt)->
    el = evt.target
    selected_value = evt.relatedTarget
    klass = selected_value.getAttribute('data-class')
    set_data(el, selected_value, board_palette_dom)
    if game_dom.querySelectorAll(".#{klass}").length >= 4
      window.hide_element(selected_value)
)

tetramino_click_handler = ->
  if not this.classList.contains('snapped')
    angle = parseInt(this.dataset.rotationAngle)
    if angle >= 270
      this.classList.remove('animate')
      angle -= 360
      this.style.setProperty('--rotation', "#{angle}deg")
      this.offsetHeight
      this.classList.add('animate')

    this.dataset.rotationAngle = angle + 90
    this.style.setProperty('--rotation', "#{this.dataset.rotationAngle}deg")

tetramino_color_click_handler = ->
  this.parentNode.querySelectorAll('.cell').forEach((c)->
    set_data(c, selected_color_icon, color_palette_dom)
  )
  if selected_color_icon
    window.hide_element(selected_color_icon)
    selected_color_icon.classList.remove('selected')
    selected_color_icon = null

document.querySelectorAll('.tetramino').forEach((t)->
  if not t.classList.contains('tet-O')
    t.dataset.rotationAngle = 0
    t.addEventListener('click', tetramino_click_handler)
)

get_tetramino_data = (el)->
  cell_size = parseFloat(getComputedStyle(el.querySelector('.cell')).width)
  range = cell_size / 2
  rotation_angle = (parseInt(el.dataset.rotationAngle) or 0) % 360

  [row_array, col_array] = [null, null]
  if el.classList.contains('tet-O')
    [row_array, col_array] = [[0...N - 1], [0...M - 1]]
  else if el.classList.contains('tet-I')
    if rotation_angle == 0
      [row_array, col_array] = [[0...N], [0...1]]
    else if rotation_angle == 90
      [row_array, col_array] = [[0...1], [0...M]]
    else if rotation_angle == 180
      [row_array, col_array] = [[0...N], [0...1]]
    else if rotation_angle == 270
      [row_array, col_array] = [[0...1], [0...M]]
  else if el.classList.contains('tet-T')
    if rotation_angle == 0
      [row_array, col_array] = [[0...N - 1], [0...M - 2]]
    else if rotation_angle == 90
      [row_array, col_array] = [[0...N - 2], [0...M - 1]]
    else if rotation_angle == 180
      [row_array, col_array] = [[0...N - 1], [0...M - 2]]
    else if rotation_angle == 270
      [row_array, col_array] = [[0...N - 2], [0...M - 1]]
  else if el.classList.contains('tet-L')
    if rotation_angle == 0
      [row_array, col_array] = [[0...N - 1], [0...M - 2]]
    else if rotation_angle == 90
      [row_array, col_array] = [[0...N - 2], [0...M - 1]]
    else if rotation_angle == 180
      [row_array, col_array] = [[0...N - 1], [0...M - 2]]
    else if rotation_angle == 270
      [row_array, col_array] = [[0...N - 2], [0...M - 1]]
  else if el.classList.contains('tet-J')
    if rotation_angle == 0
      [row_array, col_array] = [[0...N - 1], [0...M - 2]]
    else if rotation_angle == 90
      [row_array, col_array] = [[0...N - 2], [0...M - 1]]
    else if rotation_angle == 180
      [row_array, col_array] = [[0...N - 1], [0...M - 2]]
    else if rotation_angle == 270
      [row_array, col_array] = [[0...N - 2], [0...M - 1]]
  else if el.classList.contains('tet-S')
    if rotation_angle == 0
      [row_array, col_array] = [[0...N - 1], [0...M - 2]]
    else if rotation_angle == 90
      [row_array, col_array] = [[0...N - 2], [0...M - 1]]
    else if rotation_angle == 180
      [row_array, col_array] = [[0...N - 1], [0...M - 2]]
    else if rotation_angle == 270
      [row_array, col_array] = [[0...N - 2], [0...M - 1]]
  else if el.classList.contains('tet-Z')
    if rotation_angle == 0
      [row_array, col_array] = [[0...N - 1], [0...M - 2]]
    else if rotation_angle == 90
      [row_array, col_array] = [[0...N - 2], [0...M - 1]]
    else if rotation_angle == 180
      [row_array, col_array] = [[0...N - 1], [0...M - 2]]
    else if rotation_angle == 270
      [row_array, col_array] = [[0...N - 2], [0...M - 1]]

  return {
    row_array: row_array,
    col_array: col_array,
    cell_size: cell_size,
    range: range
  }

get_tetramino_indices = (el, row, col)->
  rotation_angle = (parseInt(el.dataset.rotationAngle) or 0) % 360
  cells = []
  if el.classList.contains('tet-O')
    cells = [[row, col], [row, col + 1], [row + 1, col], [row + 1, col + 1]]
  else if el.classList.contains('tet-I')
    if rotation_angle == 0
      cells = [[row, col], [row, col + 1], [row, col + 2], [row, col + 3]]
    else if rotation_angle == 90
      cells = [[row, col], [row + 1, col], [row + 2, col], [row + 3, col]]
    else if rotation_angle == 180
      cells = [[row, col], [row, col + 1], [row, col + 2], [row, col + 3]]
    else if rotation_angle == 270
      cells = [[row, col], [row + 1, col], [row + 2, col], [row + 3, col]]
  else if el.classList.contains('tet-T')
    if rotation_angle == 0
      cells = [[row, col], [row, col + 1], [row, col + 2], [row + 1, col + 1]]
    else if rotation_angle == 90
      cells = [[row, col + 1], [row + 1, col], [row + 1, col + 1], [row + 2, col + 1]]
    else if rotation_angle == 180
      cells = [[row, col + 1], [row + 1, col], [row + 1, col + 1], [row + 1, col + 2]]
    else if rotation_angle == 270
      cells = [[row, col], [row + 1, col], [row + 1, col + 1], [row + 2, col]]
  else if el.classList.contains('tet-L')
    if rotation_angle == 0
      cells = [[row, col], [row, col + 1], [row, col + 2], [row + 1, col]]
    else if rotation_angle == 90
      cells = [[row, col], [row, col + 1], [row + 1, col + 1], [row + 2, col + 1]]
    else if rotation_angle == 180
      cells = [[row, col + 2], [row + 1, col], [row + 1, col + 1], [row + 1, col + 2]]
    else if rotation_angle == 270
      cells = [[row, col], [row + 1, col], [row + 2, col], [row + 2, col + 1]]
  else if el.classList.contains('tet-J')
    if rotation_angle == 0
      cells = [[row, col], [row, col + 1], [row, col + 2], [row + 1, col + 2]]
    else if rotation_angle == 90
      cells = [[row + 2, col], [row, col + 1], [row + 1, col + 1], [row + 2, col + 1]]
    else if rotation_angle == 180
      cells = [[row, col], [row + 1, col], [row + 1, col + 1], [row + 1, col + 2]]
    else if rotation_angle == 270
      cells = [[row, col], [row, col + 1], [row + 1, col], [row + 2, col]]
  else if el.classList.contains('tet-S')
    if rotation_angle == 0
      cells = [[row, col + 1], [row, col + 2], [row + 1, col], [row + 1, col + 1]]
    else if rotation_angle == 90
      cells = [[row, col], [row + 1, col], [row + 1, col + 1], [row + 2, col + 1]]
    else if rotation_angle == 180
      cells = [[row, col + 1], [row, col + 2], [row + 1, col], [row + 1, col + 1]]
    else if rotation_angle == 270
      cells = [[row, col], [row + 1, col], [row + 1, col + 1], [row + 2, col + 1]]
  else if el.classList.contains('tet-Z')
    if rotation_angle == 0
      cells = [[row, col], [row, col + 1], [row + 1, col + 1], [row + 1, col + 2]]
    else if rotation_angle == 90
      cells = [[row, col + 1], [row + 1, col], [row + 1, col + 1], [row + 2, col]]
    else if rotation_angle == 180
      cells = [[row, col], [row, col + 1], [row + 1, col + 1], [row + 1, col + 2]]
    else if rotation_angle == 270
      cells = [[row, col + 1], [row + 1, col], [row + 1, col + 1], [row + 2, col]]

  return cells

snap_targets = (index) ->
  inner = (x, y, interaction) ->
    offset_y = window.pageYOffset or document.documentElement.scrollTop
    offset_x = window.pageXOffset or document.documentElement.scrollLeft

    outline_board_rect = outline_board.getBoundingClientRect()
    table_top = outline_board_rect.top + offset_y
    table_left = outline_board_rect.left + offset_x
    el = interaction.element
    data = get_tetramino_data(el)
    idx = 0
    for i in data.row_array
      for j in data.col_array
        if index == idx
          for [r, c] in get_tetramino_indices(el, i, j)
            if outline_board.rows[r].cells[c].getAttribute('data-number')
              return {x: Infinity, y: Infinity, range: data.range}
          return {
            x: table_left + j * data.cell_size,
            y: table_top + i * data.cell_size,
            range: data.range
          }
        idx += 1
  return inner

interact('.tetramino').draggable(
  onstart: (evt)->
    el = evt.target
    if not el.classList.contains('snapped')
      create_clone(el, tetramino_click_handler)
    el.classList.remove('animate')
    el.style.setProperty('z-index', 10000)
    number = el.getAttribute('data-number')
    if number
      outline_board.querySelectorAll("[data-number='#{number}']").forEach((e)->
        e.removeAttribute('data-number')
      )
  onmove: (evt)->
    el = evt.target
    x = (parseFloat(el.dataset.x) or 0) + evt.dx
    y = (parseFloat(el.dataset.y) or 0) + evt.dy
    el.style.transform = "translate(#{x}px, #{y}px) rotate(var(--rotation, 0))"
    el.dataset.x = x
    el.dataset.y = y
  onend: (evt)->
    el = evt.target
    snap = evt.modifiers[0]
    snapped = snap.inRange
    if snapped
      el.classList.add('snapped')
      el.style.removeProperty('z-index')
      el.removeEventListener('click', tetramino_click_handler)
      el.querySelectorAll('.cell').forEach((c)->
        c.addEventListener('click', tetramino_color_click_handler)
      )
      data = get_tetramino_data(el)
      row = Math.floor(snap.target.index / data.col_array.length)
      col = snap.target.index % data.col_array.length
      num = Math.random()
      for [r, c] in get_tetramino_indices(el, row, col)
        outline_board.rows[r].cells[c].setAttribute('data-number', num)
        el.setAttribute('data-number', num)
    else
      number = el.getAttribute('data-number')
      outline_board.querySelectorAll("[data-number='#{number}']").forEach((e)->
        e.removeAttribute('data-number')
      )
      color_class = el.querySelector('.cell').getAttribute('data-class')
      if color_class
        window.show_element(color_palette_dom.querySelector(".#{color_class}"))
      el.remove()

    game_grid.innerHTML = ''
    document.querySelectorAll('.snapped').forEach((el)->
      snapped_grid = el.querySelector('.outline-grid')
      html = snapped_grid.innerHTML
      rotation_angle = parseInt(el.getAttribute('data-rotation-angle')) or 0
      el.style.setProperty('--rotation', "0deg")
      snapped_rect = el.getBoundingClientRect()
      el.style.setProperty('--rotation', "#{rotation_angle}deg")
      source_cell_size = parseFloat(getComputedStyle(outline_board.querySelector('td')).width)
      target_cell_size = parseFloat(getComputedStyle(game_board.querySelector('td')).width)
      ratio = target_cell_size / source_cell_size
      outline_board_rect = outline_board.getBoundingClientRect()
      shift_x = (snapped_rect.left - outline_board_rect.left) * ratio
      shift_y = (snapped_rect.top - outline_board_rect.top) * ratio
      div = document.createElement('div')
      div.style.left = "#{shift_x}px"
      div.style.top = "#{shift_y}px"
      div.style.transform = "rotate(#{rotation_angle}deg)"
      [ox, oy] = getComputedStyle(el).transformOrigin.split(' ')
      div.style.transformOrigin = "#{parseFloat(ox) * ratio}px #{parseFloat(oy) * ratio}px"
      div.innerHTML = html
      game_grid.appendChild(div)
    )

  modifiers: [
    interact.modifiers.snap(
      targets: (snap_targets(i) for i in [0...9])
      relativePoints: [{x: 0, y: 0}]
    )
  ]
).styleCursor(false)

interact('#outline table').dropzone(
  accept: '.tetramino'
  overlap: 0.8,
)

nodes.forEach((node)->
  node.addEventListener('click', ->
    node.classList.toggle('disabled')
  )
)

document.addEventListener('contextmenu', (evt)->
  class_list = evt.target.classList
  if class_list.contains('tetramino') or class_list.contains('board-item')
    evt.preventDefault()
)
error_field = document.getElementById('error-box')
set_error = (error)->
  error_field.innerHTML = error
  window.show_element(error_field)
  window.hide_element(response_field)
  setTimeout(->
    window.hide_element(error_field)
  , 5000)

response_field = document.getElementById('response-box')
set_response = (response)->
  response_field.innerHTML = response
  window.show_element(response_field)
  window.hide_element(error_field)

document.getElementById('create-button').addEventListener('click', ->
  window.hide_element(error_field)
  outline = []
  outline_dom.querySelectorAll('td').forEach((e)->
    number = e.getAttribute('data-number')
    if number
      outline.push(number)
  )
  if outline.length != N * M
    set_error('Incomplete outline.')
    return

  fixed_areas = {}
  document.querySelectorAll('.snapped').forEach((e)->
    index = e.querySelector('.cell').getAttribute('data-index')
    if index
      fixed_areas[e.getAttribute('data-number')] = index
  )

  board = []
  game_dom.querySelectorAll('td').forEach((e)->
    index = e.getAttribute('data-index')
    if index
      board.push(index)
  )
  if board.length != M * N
    set_error('Incomplete board.')
    return

  disabled_nodes = []
  nodes.forEach((n)->
    if n.classList.contains('disabled')
      disabled_nodes.push(n.getAttribute('data-value'))
  )
  if disabled_nodes.length == (M - 1) * (N - 1)
    set_error('No active nodes.')
    return

  send_request('/post-create/', {
    outline: outline.join(','),
    fixed_areas: ("#{k}:#{v}" for k, v of fixed_areas).join(','),
    board: board.join(','),
    nodes: disabled_nodes.join(',')
  }, 'POST', (data)->
    if data['error']
      set_error(data['error'])
    if data['url']
      set_response(data['url'])
  )
)
