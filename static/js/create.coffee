selected = {color_icon: null, board_item: null}
game_dom = document.querySelector('#game-container')

color_palette_dom = document.getElementById("color-palette")
board_palette_dom = document.getElementById("board-palette")

item_click_handler = (property) ->
  if selected[property]
    selected[property].classList.remove('selected')
    if selected[property] == this
      selected[property] = null
      return
  this.classList.add('selected')
  selected[property] = this


remove_data = (el, palette)->
  color_class = el.getAttribute('data-class')
  if color_class
    el.classList.remove(color_class)
    palette.querySelector(".#{color_class}").style.display = 'flex'
  el.removeAttribute('data-class')
  el.removeAttribute('data-index')
  el.removeAttribute('data-name')
  span = el.querySelector('span')
  if span
    span.innerHTML = ''

set_data = (el, klass, index, name)->
  cell_color_class = el.getAttribute('data-class')
  if cell_color_class
    el.classList.remove(cell_color_class)
  el.classList.add(klass)
  el.setAttribute('data-class', klass)
  el.setAttribute('data-index', index)
  el.setAttribute('data-name', name)
  if name
    el.querySelector('span').innerHTML = name

for item in color_palette_dom.getElementsByClassName('color-icon')
  item.addEventListener('click', ->
    item_click_handler.call(this, 'color_icon')
  )

game_dom.querySelectorAll('td').forEach((cell) ->
  cell.addEventListener("click", ->
    selected_value = selected['board_item']
    if selected_value
      cell_color_class = cell.getAttribute('data-class')
      if cell_color_class
        board_palette_dom.querySelector(".#{cell_color_class}").style.display = 'flex'
      klass = selected_value.getAttribute('data-class')
      index = selected_value.getAttribute('data-index')
      name = selected_value.getAttribute('data-name')
      set_data(cell, klass, index, name)

      selected_value.classList.remove('selected')
      if game_dom.querySelectorAll(".#{klass}").length >= 4
        selected_value.style.display = 'none'
      selected['board_item'] = null
    else
      cell_color_class = cell.getAttribute('data-class')
      if cell_color_class
        remove_data(cell, board_palette_dom)
  )
  )

document.querySelectorAll('.node').forEach((node)->
  node.addEventListener('click', ->
    node.classList.toggle('disabled')
  )
)

create_clone = (source, click_listener = null)->
  clone = source.cloneNode(true)
  clone.style.position = 'absolute'
  clone.style.left = source.offsetLeft + 'px'
  clone.style.top = source.offsetTop + 'px'
  if click_listener
    clone.addEventListener('click', click_listener)
  source.after(clone)
  return clone

active_item_clone = null
interact('.board-item').draggable(
  onstart: (evt)->
    active_item_clone = create_clone(evt.target)
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
    active_item_clone.remove()
    active_item_clone = null
).styleCursor(false)

interact('#game-container td').dropzone(
  accept: '.board-item'
  overlap: 0.75,
  ondrop: (evt)->
    el = evt.target
    cell_class = el.getAttribute('data-class')
    if cell_class
      board_palette_dom.querySelector(".#{cell_class}").style.display = 'flex'
    selected_value = evt.relatedTarget
    klass = selected_value.getAttribute('data-class')
    index = selected_value.getAttribute('data-index')
    name = selected_value.getAttribute('data-name')
    set_data(el, klass, index, name)
    if game_dom.querySelectorAll(".#{klass}").length >= 4
      selected_value.style.display = 'none'
)

tetramino_click_handler = ->
  if this.dataset.isDragging == 'true'
    this.dataset.isDragging = false
  else
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
  if this.dataset.isDragging == 'true'
    this.dataset.isDragging = false
  else
    color_class = this.querySelector('.cell').getAttribute('data-class')
    if color_class
      this.querySelectorAll('.cell').forEach((c)->
        remove_data(c, color_palette_dom)
      )
      color_palette_dom.querySelector("[data-class='#{color_class}']").style.display = 'inline-block'
    icon = selected['color_icon']
    if icon
      klass = icon.getAttribute('data-class')
      index = icon.getAttribute('data-index')
      name = icon.getAttribute('data-name')
      this.querySelectorAll('.cell').forEach((c)->
        set_data(c, klass, index, name)
      )
      icon.classList.remove('selected')
      icon.style.display = 'none'
      selected['color_icon'] = null

document.querySelectorAll('.tetramino').forEach((t)->
  if not t.parentNode.classList.contains('tet-O')
    t.dataset.rotationAngle = 0
    t.addEventListener('click', tetramino_click_handler)
)

outline_table = document.querySelector('#outline table')
N = outline_table.rows.length
M = outline_table.rows[0].cells.length

get_tetramino_data = (el)->
  cell_size = el.querySelector('.cell').getBoundingClientRect().width
  range = cell_size / 2
  rotation_angle = (parseInt(el.dataset.rotationAngle) or 0) % 360

  [row_array, col_array] = [null, null]
  if el.parentNode.classList.contains('tet-O')
    [row_array, col_array] = [[0...N - 1], [0...M - 1]]
  else if el.parentNode.classList.contains('tet-I')
    if rotation_angle == 0
      [row_array, col_array] = [[0...N], [0...1]]
    else if rotation_angle == 90
      [row_array, col_array] = [[0...1], [0...M]]
    else if rotation_angle == 180
      [row_array, col_array] = [[0...N], [0...1]]
    else if rotation_angle == 270
      [row_array, col_array] = [[0...1], [0...M]]
  else if el.parentNode.classList.contains('tet-T')
    if rotation_angle == 0
      [row_array, col_array] = [[0...N - 1], [0...M - 2]]
    else if rotation_angle == 90
      [row_array, col_array] = [[0...N - 2], [0...M - 1]]
    else if rotation_angle == 180
      [row_array, col_array] = [[0...N - 1], [0...M - 2]]
    else if rotation_angle == 270
      [row_array, col_array] = [[0...N - 2], [0...M - 1]]
  else if el.parentNode.classList.contains('tet-L')
    if rotation_angle == 0
      [row_array, col_array] = [[0...N - 1], [0...M - 2]]
    else if rotation_angle == 90
      [row_array, col_array] = [[0...N - 2], [0...M - 1]]
    else if rotation_angle == 180
      [row_array, col_array] = [[0...N - 1], [0...M - 2]]
    else if rotation_angle == 270
      [row_array, col_array] = [[0...N - 2], [0...M - 1]]
  else if el.parentNode.classList.contains('tet-J')
    if rotation_angle == 0
      [row_array, col_array] = [[0...N - 1], [0...M - 2]]
    else if rotation_angle == 90
      [row_array, col_array] = [[0...N - 2], [0...M - 1]]
    else if rotation_angle == 180
      [row_array, col_array] = [[0...N - 1], [0...M - 2]]
    else if rotation_angle == 270
      [row_array, col_array] = [[0...N - 2], [0...M - 1]]
  else if el.parentNode.classList.contains('tet-S')
    if rotation_angle == 0
      [row_array, col_array] = [[0...N - 1], [0...M - 2]]
    else if rotation_angle == 90
      [row_array, col_array] = [[0...N - 2], [0...M - 1]]
    else if rotation_angle == 180
      [row_array, col_array] = [[0...N - 1], [0...M - 2]]
    else if rotation_angle == 270
      [row_array, col_array] = [[0...N - 2], [0...M - 1]]
  else if el.parentNode.classList.contains('tet-Z')
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
  if el.parentNode.classList.contains('tet-O')
    cells = [[row, col], [row, col + 1], [row + 1, col], [row + 1, col + 1]]
  else if el.parentNode.classList.contains('tet-I')
    if rotation_angle == 0
      cells = [[row, col], [row, col + 1], [row, col + 2], [row, col + 3]]
    else if rotation_angle == 90
      cells = [[row, col], [row + 1, col], [row + 2, col], [row + 3, col]]
    else if rotation_angle == 180
      cells = [[row, col], [row, col + 1], [row, col + 2], [row, col + 3]]
    else if rotation_angle == 270
      cells = [[row, col], [row + 1, col], [row + 2, col], [row + 3, col]]
  else if el.parentNode.classList.contains('tet-T')
    if rotation_angle == 0
      cells = [[row, col], [row, col + 1], [row, col + 2], [row + 1, col + 1]]
    else if rotation_angle == 90
      cells = [[row, col + 1], [row + 1, col], [row + 1, col + 1], [row + 2, col + 1]]
    else if rotation_angle == 180
      cells = [[row, col + 1], [row + 1, col], [row + 1, col + 1], [row + 1, col + 2]]
    else if rotation_angle == 270
      cells = [[row, col], [row + 1, col], [row + 1, col + 1], [row + 2, col]]
  else if el.parentNode.classList.contains('tet-L')
    if rotation_angle == 0
      cells = [[row, col], [row, col + 1], [row, col + 2], [row + 1, col]]
    else if rotation_angle == 90
      cells = [[row, col], [row, col + 1], [row + 1, col + 1], [row + 2, col + 1]]
    else if rotation_angle == 180
      cells = [[row, col + 2], [row + 1, col], [row + 1, col + 1], [row + 1, col + 2]]
    else if rotation_angle == 270
      cells = [[row, col], [row + 1, col], [row + 2, col], [row + 2, col + 1]]
  else if el.parentNode.classList.contains('tet-J')
    if rotation_angle == 0
      cells = [[row, col], [row, col + 1], [row, col + 2], [row + 1, col + 2]]
    else if rotation_angle == 90
      cells = [[row + 2, col], [row, col + 1], [row + 1, col + 1], [row + 2, col + 1]]
    else if rotation_angle == 180
      cells = [[row, col], [row + 1, col], [row + 1, col + 1], [row + 1, col + 2]]
    else if rotation_angle == 270
      cells = [[row, col], [row, col + 1], [row + 1, col], [row + 2, col]]
  else if el.parentNode.classList.contains('tet-S')
    if rotation_angle == 0
      cells = [[row, col + 1], [row, col + 2], [row + 1, col], [row + 1, col + 1]]
    else if rotation_angle == 90
      cells = [[row, col], [row + 1, col], [row + 1, col + 1], [row + 2, col + 1]]
    else if rotation_angle == 180
      cells = [[row, col + 1], [row, col + 2], [row + 1, col], [row + 1, col + 1]]
    else if rotation_angle == 270
      cells = [[row, col], [row + 1, col], [row + 1, col + 1], [row + 2, col + 1]]
  else if el.parentNode.classList.contains('tet-Z')
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
    table_rect = outline_table.getBoundingClientRect()
    offset_y = window.pageYOffset or document.documentElement.scrollTop
    offset_x = window.pageXOffset or document.documentElement.scrollLeft

    table_top = table_rect.top + offset_y
    table_left = table_rect.left + offset_x

    el = interaction.element
    data = get_tetramino_data(el)
    idx = 0
    for i in data.row_array
      for j in data.col_array
        if index == idx
          for [r, c] in get_tetramino_indices(el, i, j)
            if outline_table.rows[r].cells[c].getAttribute('data-number')
              return {x:Infinity, y: Infinity, range: data.range}
          return{
            x: table_left + j * data.cell_size,
            y: table_top + i * data.cell_size,
            range: data.range
          }
        idx += 1

  return inner
interact('.tetramino').draggable(
  onstart: (evt)->
    el = evt.target
    if not el.classList.contains('placed')
      create_clone(el, tetramino_click_handler)
    el.classList.remove('animate')
    el.style.setProperty('z-index', 10000)
    el.dataset.isDragging = true
    number =el.getAttribute('data-number')
    if number
      outline_table.querySelectorAll("[data-number='#{number}']").forEach((e)->
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
      el.classList.add('placed')
      el.style.removeProperty('z-index')
      el.removeEventListener('click', tetramino_click_handler)
      el.addEventListener('click', tetramino_color_click_handler)
      data = get_tetramino_data(el)
      row = Math.floor(snap.target.index / data.col_array.length)
      col = snap.target.index % data.col_array.length
      num = Math.random()
      for [r, c] in get_tetramino_indices(el, row, col)
        outline_table.rows[r].cells[c].setAttribute('data-number', num)
        el.setAttribute('data-number', num)
    else
      outline_table.querySelectorAll("[data-number='#{el.getAttribute('data-number')}']").forEach((e)->
        e.removeAttribute('data-number')
      )
      color_class = el.querySelector('.cell').getAttribute('data-class')
      if color_class
        el.querySelectorAll('.cell').forEach((c)->
          remove_data(c, color_palette_dom)
        )
        color_palette_dom.querySelector("[data-class='#{color_class}']").style.display = 'inline-block'
      el.remove()

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