selected_outline = null
selected = {color_icon: null, board_item: null}
outlines_dom = [...document.querySelectorAll('#outlines > .outline-container')]
outline_dom = document.querySelector('#outline > .outline-container')
game_dom = document.querySelector('#game-container')
outline_hidden_dom = document.querySelector('#outline-hidden > .outline-container')

color_palette_dom = document.getElementById("color-palette")
board_palette_dom = document.getElementById("board-palette")

copy_outline = (src, target, erase_data = false)->
  target.setAttribute('data-index', src.getAttribute('data-index'))
  src_table = src.querySelector('table')
  target_table = target.querySelector('table')
  for i in [0...src_table.rows.length]
    for j in [0...src_table.rows[0].cells.length]
      target_cell = target_table.rows[i].cells[j]
      src_cell = src_table.rows[i].cells[j]
      target_cell.setAttribute('data-value', src_cell.getAttribute('data-value'))
      if erase_data
        remove_data(target_cell, color_palette_dom, 'color-icon', 'color_icon')
  target.querySelector('.outline-grid').innerHTML = src.querySelector('.outline-grid').innerHTML

outlines_dom.forEach((outline)->
  outline.addEventListener('click', ->
    if selected_outline
      selected_outline.classList.remove('selected')
      if selected_outline == this
        copy_outline(outline_hidden_dom, outline_dom, true)
        copy_outline(outline_hidden_dom, game_dom)
        selected_outline = null
        return
    this.classList.add('selected')
    selected_outline = this
    copy_outline(selected_outline, outline_dom, true)
    copy_outline(selected_outline, game_dom)
  )
)

item_click_handler = (property) ->
  if selected[property]
    selected[property].classList.remove('selected')
    if selected[property] == this
      selected[property] = null
      return
  this.classList.add('selected')
  selected[property] = this


remove_data = (cell, palette, icon_class, key)->
  color_class = cell.getAttribute('data-class')
  if color_class
    cell.classList.remove(color_class)
    palette.querySelector(".#{color_class}").style.display = 'flex'
  cell.removeAttribute('data-class')
  cell.removeAttribute('data-index')
  cell.removeAttribute('data-name')
  span = cell.querySelector('span')
  if span
    span.innerHTML = ''

set_data = (cell, klass, index, name)->
  cell_color_class = cell.getAttribute('data-class')
  if cell_color_class
    cell.classList.remove(cell_color_class)
  cell.classList.add(klass)
  cell.setAttribute('data-class', klass)
  cell.setAttribute('data-index', index)
  cell.setAttribute('data-name', name)
  if name
    cell.querySelector('span').innerHTML = name


init_handlers = (key, icon_class, dom, palette_dom)->
  if key == 'color_icon'
    for item in palette_dom.getElementsByClassName(icon_class)
      item.addEventListener('click', ->
        item_click_handler.call(this, key)
      )
  dom.querySelectorAll('td').forEach((cell) ->
    cell.addEventListener("click", ->
      value = cell.getAttribute('data-value')
      selected_value = selected[key]
      if selected_value
        cell_color_class = cell.getAttribute('data-class')
        if cell_color_class
          palette_dom.querySelector(".#{cell_color_class}").style.display = 'flex'
        klass = selected_value.getAttribute('data-class')
        index = selected_value.getAttribute('data-index')
        name = selected_value.getAttribute('data-name')
        if key == 'color_icon'
          dom.querySelectorAll("td[data-value='#{value}']").forEach((c)->
            set_data(c, klass, index, name)
          )
        else
          set_data(cell, klass, index, name)

        selected_value.classList.remove('selected')
        if dom.querySelectorAll(".#{klass}").length >= 4
          selected_value.style.display = 'none'
        selected[key] = null
      else
        cell_color_class = cell.getAttribute('data-class')
        if cell_color_class
          if key == 'color_icon'
            dom.querySelectorAll("td[data-value='#{value}']").forEach((c)->
              remove_data(c, palette_dom, icon_class, key)
            )
          else
            remove_data(cell, palette_dom, icon_class, key)
    )
  )

for [key, icon_class, dom, palette_dom] in [['color_icon', 'color-icon', outline_dom, color_palette_dom],
  ['board_item', 'board-item', game_dom, board_palette_dom]]
  init_handlers(key, icon_class, dom, palette_dom)

document.querySelectorAll('.node').forEach((node)->
  node.addEventListener('click', ->
    node.classList.toggle('disabled')
  )
)

create_clone = (source)->
  clone = source.cloneNode(true)
  clone.style.position = 'absolute'
  clone.style.left = source.offsetLeft + 'px'
  clone.style.top = source.offsetTop + 'px'
  source.before(clone)
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

document.querySelectorAll('.tetramino').forEach((t)->
  if not t.parentNode.classList.contains('tet-O')
    t.dataset.rotationAngle = 0
    t.addEventListener('click', ->
      if t.dataset.isDragging == 'true'
        t.dataset.isDragging = false
      else
        t.dataset.rotationAngle = parseInt(t.dataset.rotationAngle) + 90
        t.style.setProperty('--rotation', "#{t.dataset.rotationAngle}deg")
    )
)
outline_table = document.querySelector('#outline table')
snap_targets = (index) ->
  inner = (x, y, interaction) ->
    el = interaction.element
    console.log(x - el.style.left,y- el.style.top)
    cell_size = el.querySelector('.cell').getBoundingClientRect().width
    tableRect = outline_table.getBoundingClientRect()
    console.log(tableRect)
    offsetY  = window.pageYOffset or document.documentElement.scrollTop
    offsetX = window.pageXOffset or document.documentElement.scrollLeft
    points  = []
    for i in [0...outline_table.rows.length - 1]
      for j in [0...outline_table.rows[0].cells.length - 1]
        points.push(
          x: tableRect.left + offsetX + (j + 1) * cell_size,
          y: tableRect.top + offsetY + (i + 1) * cell_size
        )
    return points[index]
  return inner
interact('.tetramino').draggable(
  onstart: (evt)->
    el = evt.target
    el.classList.remove('animate')
    el.dataset.isDragging = true
    active_item_clone = create_clone(el)
  onmove: (evt)->
    el = evt.target
    x = (parseFloat(el.dataset.x) or 0) + evt.dx
    y = (parseFloat(el.dataset.y) or 0) + evt.dy
    el.style.transform = "translate(#{x}px, #{y}px) rotate(var(--rotation, 0))"
    el.dataset.x = x
    el.dataset.y = y
  onend: (evt)->
    el = evt.target
    el.style.transform = "rotate(var(--rotation, 0))"
    el.removeAttribute('data-x')
    el.removeAttribute('data-y')
    el.offsetHeight
    el.classList.add('animate')
    active_item_clone.remove()
    active_item_clone = null
  modifiers:[
    interact.modifiers.snap(
      targets: (snap_targets(i) for i in [0...9] if snap_targets(i))
      range: 20
      relativePoints: [{ x: 0.5, y: 0.5 }]
    )
  ]

).styleCursor(false)

interact('#outline table').dropzone(
    accept: '.tetramino'
    overlap: 0.8,
    ondrop: (evt) ->
      tetramino = evt.relatedTarget
      cell = evt.target
      cell.parentNode.querySelector('.outline-grid').innerHTML = tetramino.querySelector('.outline-grid').innerHTML
      console.log(cell.getBoundingClientRect())
      console.log(tetramino.getBoundingClientRect())
)