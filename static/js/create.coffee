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
      selected_outline.classList.remove('selected');
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
    selected[property].classList.remove('selected');
    if selected[property] == this
      selected[property] = null
      return
  this.classList.add('selected')
  selected[property] = this


insert_icon = (color_class, index, name, palette, icon_class, key)->
  index = parseInt(index)
  new_icon = document.createElement('div')
  new_icon.classList.add(icon_class)
  new_icon.classList.add(color_class)
  new_icon.setAttribute('data-class', color_class)
  new_icon.setAttribute('data-index', index)
  new_icon.setAttribute('data-name', name)
  new_icon.innerHTML = name
  new_icon.addEventListener('click', ->
    item_click_handler.call(this, key)
  )
  inserted = false
  for icon in palette.getElementsByClassName(icon_class)
    idx = parseInt(icon.getAttribute('data-index'))
    if idx >= index
      inserted = true
      if idx != index
        icon.before(new_icon)
      break

  if not inserted
    palette.appendChild(new_icon)

remove_data = (cell, palette, icon_class, key)->
  color_class = cell.getAttribute('data-class')
  if color_class
    cell.classList.remove(color_class)
    insert_icon(cell.getAttribute('data-class'),
      cell.getAttribute('data-index'), cell.getAttribute('data-name'), palette,
      icon_class, key)
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
          insert_icon(cell_color_class, cell.getAttribute('data-index'), cell.getAttribute('data-name'),
            palette_dom, icon_class, key)
        klass = selected_value.getAttribute('data-class')
        index = selected_value.getAttribute('data-index')
        name = selected_value.getAttribute('data-name')
        if key == 'color_icon'
          dom.querySelectorAll("td[data-value='#{value}']").forEach((c)->
            set_data(c, klass, index, name)
          )
        else
          set_data(cell, klass, index, name)
        if dom.querySelectorAll(".#{klass}").length >= 4
          selected_value.remove()
        else
          selected_value.classList.remove('selected')
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