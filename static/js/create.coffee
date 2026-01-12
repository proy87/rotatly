selected_outline = null
selected_color_icon = null
outlines_dom = [...document.querySelectorAll('#outlines > .outline-container')]
outline_dom = document.querySelector('#outline > .outline-container')
outline_hidden_dom = document.querySelector('#outline-hidden > .outline-container')

copy_outline = (src, target)->
  target.setAttribute('data-index', src.getAttribute('data-index'))
  src_table = src.querySelector('table')
  target_table = target.querySelector('table')
  for i in [0...src_table.rows.length]
    for j in [0...src_table.rows[0].cells.length]
      target_cell = target_table.rows[i].cells[j]
      src_cell = src_table.rows[i].cells[j]
      target_cell.setAttribute('data-value', src_cell.getAttribute('data-value'))
      remove_color_class(target_cell)
  target.querySelector('.outline-grid').innerHTML = src.querySelector('.outline-grid').innerHTML

outlines_dom.forEach((outline)->
  outline.addEventListener('click', ->
    if selected_outline
      selected_outline.classList.remove('selected');
      if selected_outline == this
        copy_outline(outline_hidden_dom, outline_dom)
        selected_outline = null
        return
    this.classList.add('selected')
    selected_outline = this
    copy_outline(selected_outline, outline_dom)
  )
)

color_icon_click_handler = ->
  if selected_color_icon
    selected_color_icon.classList.remove('selected');
    if selected_color_icon == this
      selected_color_icon = null
      return
  this.classList.add('selected')
  selected_color_icon = this

palette_dom = document.getElementById("color-palette")
color_icons_dom = palette_dom.getElementsByClassName('color-icon')


for icon in color_icons_dom
  icon.addEventListener('click', color_icon_click_handler)


insert_color_icon = (color_class, index)->
  index = parseInt(index)
  color_icon = document.createElement('div')
  color_icon.classList.add('color-icon')
  color_icon.classList.add(color_class)
  color_icon.setAttribute('data-color-class', color_class)
  color_icon.setAttribute('data-index', index)
  color_icon.addEventListener('click', color_icon_click_handler)
  inserted = false
  for icon in color_icons_dom
    idx = parseInt(icon.getAttribute('data-index'))
    if idx >= index
      inserted = true
      if idx != index
        icon.before(color_icon)
      break


  if not inserted
    palette_dom.appendChild(color_icon)

outline_cells_selector = "#outline td"

remove_color_class = (cell)->
  color_class = cell.getAttribute('data-color-class')
  if color_class
    cell.classList.remove(color_class)
    insert_color_icon(color_class, cell.getAttribute('data-color-index'))
  cell.removeAttribute('data-color-class')
  cell.removeAttribute('data-color-index')

set_color_class = (cell, color_class, color_index)->
  cell_color_class = cell.getAttribute('data-color-class')
  if cell_color_class
    cell.classList.remove(cell_color_class)
  cell.classList.add(color_class)
  cell.setAttribute('data-color-class', color_class)
  cell.setAttribute('data-color-index', color_index)


document.querySelectorAll(outline_cells_selector).forEach((cell) ->
  cell.addEventListener("click", ->
    value = cell.getAttribute('data-value')
    if selected_color_icon
      cell_color_class = cell.getAttribute('data-color-class')
      if cell_color_class
        insert_color_icon(cell_color_class, cell.getAttribute('data-color-index'))
      color_class = selected_color_icon.getAttribute('data-color-class')
      color_index = selected_color_icon.getAttribute('data-index')
      document.querySelectorAll(outline_cells_selector + "[data-value='#{value}']").forEach((c)->
        set_color_class(c, color_class, color_index)
      )
      selected_color_icon.remove()
      selected_color_icon = null
    else
      cell_color_class = cell.getAttribute('data-color-class')
      if cell_color_class
        document.querySelectorAll(outline_cells_selector + "[data-value='#{value}']").forEach((c)->
          remove_color_class(c)
        )
  )
)