visit_time = new Date()
start_time = visit_time
end_time = start_time

board = document.getElementById('board')
table = board.querySelector('table')

N = table.rows.length
M = table.rows[0].cells.length
game_completed = false
in_animation = false
animated = false
in_demo = false
moves = []

moves_made_num_dom = document.getElementById('moves-made-num')
undo_button = document.getElementById('undo-move')
restart_button = document.getElementById('restart-game')
moves_sequence_dom = document.getElementById('moves-sequence')
one_less_move_dom = document.getElementById('one-less-move')
moves_num_dom = document.getElementById('moves-num')
active_nodes_dom = [...document.querySelectorAll('.node.active')]


hold_timer = null
hold_duration = 500

is_sliding = false
slided_cells = []

hide_element = (el)->
  display = window.getComputedStyle(el, null).display
  if display != 'none'
    el.setAttribute('data-display', display)
  el.style.display = 'none'

show_element = (el)->
  display = window.getComputedStyle(el, null).display
  if display == 'none'
    el.style.display = el.getAttribute('data-display') or 'block'

get_request = (url, data)->
  params = []
  for k, v of data
    params.push("#{k}=#{v}")
  await fetch(url + '?' + params.join('&'))

a2a_config.callbacks = [
  share: (share_data)->
    title = null
    url = null
    if moves.length
      if check()
        title = "Rotatly ##{game_index} in #{moves.length} moves"
      else
        title = "Rotatly ##{game_index}"
      rcw = new RegExp(cw_symbol, 'g')
      rccw = new RegExp(ccw_symbol, 'g')
      url = canonical_url + "?moves=#{moves.join('').replace(rcw, '%E2%86%BB').replace(rccw, '%E2%86%BA')}"
    else
      title = "Rotatly"
      url = today_url

    get_request(track_url, {
      game_index: game_index,
      init_time: (start_time - visit_time) / 1000,
      game_time: (end_time - start_time) / 1000,
      moves: moves.join(''),
      length: moves.length,
      share: share_data.service
    })

    return {
      title: title,
      description: 'Rotate the cells until you get the correct outline.',
      url: url
    }
]
rotate = (row, col, cw)->
  top_left = document.getElementById("cell-#{row}-#{col}")
  top_right = document.getElementById("cell-#{row}-#{col + 1}")
  bottom_left = document.getElementById("cell-#{row + 1}-#{col}")
  bottom_right = document.getElementById("cell-#{row + 1}-#{col + 1}")
  a = top_left.innerHTML
  b = top_right.innerHTML
  c = bottom_left.innerHTML
  d = bottom_right.innerHTML
  top_left.innerHTML = if cw then c else b
  top_right.innerHTML = if cw then a else d
  bottom_left.innerHTML = if cw then d else a
  bottom_right.innerHTML = if cw then b else c

  a = top_left.className
  b = top_right.className
  c = bottom_left.className
  d = bottom_right.className
  top_left.className = if cw then c else b
  top_right.className = if cw then a else d
  bottom_left.className = if cw then d else a
  bottom_right.className = if cw then b else c

  a = top_left.getAttribute('data-value')
  b = top_right.getAttribute('data-value')
  c = bottom_left.getAttribute('data-value')
  d = bottom_right.getAttribute('data-value')
  top_left.setAttribute('data-value', if cw then c else b)
  top_right.setAttribute('data-value', if cw then a else d)
  bottom_left.setAttribute('data-value', if cw then d else a)
  bottom_right.setAttribute('data-value', if cw then b else c)

check = ->
  for index in [0...N * M]
    row = Math.floor(index / M)
    col = index % M
    elem = document.getElementById("cell-#{row}-#{col}")
    value = parseInt(elem.getAttribute('data-value'))
    if outline[index] < 0 and value != outline[index]
      return false
    for index1 in [index + 1 ... N * M]
      row1 = Math.floor(index1 / M)
      col1 = index1 % M
      elem1 = document.getElementById("cell-#{row1}-#{col1}")
      value1 = parseInt(elem1.getAttribute('data-value'))
      if !(value != value1) != !(outline[index] != outline[index1])
        return false
  return true

animate = (value, row, col, cw, undo = false, demo = false, callback = null) ->
  if in_animation
    return
  in_animation = true
  animated = true
  tl = document.getElementById("cell-#{row}-#{col}")
  tr = document.getElementById("cell-#{row}-#{col + 1}")
  br = document.getElementById("cell-#{row + 1}-#{col + 1}")
  bl = document.getElementById("cell-#{row + 1}-#{col}")

  finished = 0
  cells = [tl, tr, br, bl]
  transition_callback = (e)->
    if e.propertyName == 'transform'
      finished += 1
      if finished == cells.length
        for c in cells
          c.classList.remove('animate')
          c.classList.add('non-animate')
          c.removeEventListener('transitionend', transition_callback)
        tl.classList.remove(if cw then 'move-right' else 'move-down')
        tr.classList.remove(if cw then 'move-down' else 'move-left')
        br.classList.remove(if cw then 'move-left' else 'move-up')
        bl.classList.remove(if cw then 'move-up' else 'move-right')
        for c in cells
          c.offsetHeight
        rotate(row, col, cw)
        if not undo
          moves.push("#{value}#{if cw then cw_symbol else ccw_symbol}")
          moves_sequence_dom.innerHTML = if moves.length then moves.join(' ') else 'no moves'
          if not demo
            undo_button.removeAttribute('disabled')
            restart_button.removeAttribute('disabled')

        number_of_moves = moves.length
        if number_of_moves == 1 and not undo
          start_time = new Date()
        moves_made_num_dom.innerHTML = number_of_moves
        solved = check()
        if not demo and (number_of_moves >= moves_max_num or solved)
          end_time = new Date()
          game_completed = true
          active_nodes_dom.forEach((node)->
            hide_element(node)
          )
          hide_element(undo_button)
          if solved
            one_less_move_dom.innerHTML = number_of_moves - 1
            moves_num_dom.innerHTML = number_of_moves
            block = document.getElementById("#{if number_of_moves > moves_min_num then 'non-' else ''}min-text")
          else
            block = document.getElementById("non-solve-text")
          show_element(block)

          document.getElementById("share-container").style.display = 'flex'

          get_request(track_url, {
            game_index: game_index, init_time: (start_time - visit_time) / 1000,
            game_time: (end_time - start_time) / 1000, moves: moves.join(''), length: number_of_moves
          })

        in_animation = false

        if callback
          callback()

  for cell in cells
    cell.classList.remove('non-animate')
    cell.classList.add('animate')
    cell.addEventListener('transitionend', transition_callback)

  tl.classList.add(if cw then 'move-right' else 'move-down')
  tr.classList.add(if cw then 'move-down' else 'move-left')
  br.classList.add(if cw then 'move-left' else 'move-up')
  bl.classList.add(if cw then 'move-up' else 'move-right')

undo = (callback)->
  if moves.length > 0
    elem = moves.pop()
    moves_sequence_dom.innerHTML = if moves.length then moves.join(' ') else 'no moves'
    value = elem.slice(0, -1)
    node = active_nodes_dom.filter((n)-> n.getAttribute('data-value') == "#{value}")[0]
    if node
      row = parseInt(node.getAttribute('data-row'))
      col = parseInt(node.getAttribute('data-col'))
      animate(value, row, col, elem.slice(-1) != cw_symbol, true, false, if callback then callback else undo)

make_move = ->
  setTimeout(->
    if pre_moves.length > 0
      undo_button.setAttribute('disabled', true)
      restart_button.setAttribute('disabled', true)
      elem = pre_moves.shift()
      value = elem[0]
      cw = elem[1]
      node = active_nodes_dom.filter((n)-> n.getAttribute('data-value') == "#{value}" and n.getAttribute(if cw then 'data-cw' else 'data-ccw') == "true")[0]
      if node
        row = parseInt(node.getAttribute('data-row'))
        col = parseInt(node.getAttribute('data-col'))
        animate(value, row, col, cw, false, true, make_move)
      else
        in_demo = false
        undo_button.removeAttribute('disabled')
        restart_button.removeAttribute('disabled')
    else
      in_demo = false
      undo_button.removeAttribute('disabled')
      restart_button.removeAttribute('disabled')
  , 700)

if pre_moves.length > 0
  in_demo = true
  make_move()

active_nodes_dom.forEach((node)->
  value = parseInt(node.getAttribute('data-value'))
  row = parseInt(node.getAttribute('data-row'))
  col = parseInt(node.getAttribute('data-col'))
  node.addEventListener('click', ->
    if not animated
      animate(value, row, col, true)
  )
  node.addEventListener('pointerdown', ->
    if not in_animation
      animated = false
      hold_timer = setTimeout(->
        clearTimeout(hold_timer)
        hold_timer = null
        if not animated
          animate(value, row, col, false)
      , hold_duration
      )
  )
  node.addEventListener('pointerup pointerleave pointercancel', ->
    if hold_timer
      clearTimeout(hold_timer)
      hold_timer = null
  )
)

document.addEventListener('contextmenu', (evt)->
  node = evt.target
  if board.contains(node)
    evt.preventDefault()
    if not animated and active_nodes_dom.includes(node)
      value = parseInt(node.getAttribute('data-value'))
      row = parseInt(node.getAttribute('data-row'))
      col = parseInt(node.getAttribute('data-col'))
      animate(value, row, col, false)
)

undo_button.addEventListener('click', ->
  undo_button.setAttribute('disabled', true)
  restart_button.setAttribute('disabled', true)
  undo(->
    if moves.length > 0
      undo_button.removeAttribute('disabled')
      restart_button.removeAttribute('disabled')
  )
)
restart_button.addEventListener('click', ->
  [...document.getElementById("non-solve-text").parentElement.children].forEach((node)->
    hide_element(node)
  )
  active_nodes_dom.forEach((node)-> show_element(node))
  undo_button.setAttribute('disabled', true)
  show_element(undo_button)
  restart_button.setAttribute('disabled', true)
  game_completed = false
  undo()
)

get_cell = (target)->
  if not table.contains(target)
    return null
  if target.tagName != 'TD'
    target = target.closest('td')
  return target

validate = ->
  n = slided_cells.length
  if n < 2
    return true
  for i in [0...n - 1]
    current = slided_cells[i]
    next = slided_cells[i + 1]
    current_row = parseInt(current.getAttribute('data-row'))
    current_col = parseInt(current.getAttribute('data-col'))
    next_row = parseInt(next.getAttribute('data-row'))
    next_col = parseInt(next.getAttribute('data-col'))
    if Math.abs(current_row - next_row) + Math.abs(current_col - next_col) != 1
      return false
  return true

get_node_and_direction = ->
  possible_nodes = [1..(N - 1) * (M - 1)]
  direction = []
  for idx in [0...slided_cells.length]
    cell = slided_cells[idx]
    row = parseInt(cell.getAttribute('data-row'))
    col = parseInt(cell.getAttribute('data-col'))
    if idx > 0
      prev_cell = slided_cells[idx - 1]
      prev_row = parseInt(prev_cell.getAttribute('data-row'))
      prev_col = parseInt(prev_cell.getAttribute('data-col'))
      if prev_row - row == 1
        direction.push('up')
      else if prev_row - row == -1
        direction.push('down')
      else if prev_col - col == 1
        direction.push('left')
      else if prev_col - col == -1
        direction.push('right')

    current_nodes = []
    for i in [0, -1]
      for j in [0, -1]
        elem = active_nodes_dom.filter((n) -> n.getAttribute('data-row') == "#{row + i}" and n.getAttribute('data-col') == "#{col + j}")[0]
        if elem
          current_nodes.push(parseInt(elem.getAttribute('data-value')))
    possible_nodes = possible_nodes.filter((v)->current_nodes.indexOf(v) >= 0)
  nn = possible_nodes.length
  if nn == 0
    return false
  if possible_nodes.length == 1
    v = possible_nodes[0]
    if direction.length > 1
      if direction[0] == 'up'
        return [v, direction[1] == 'right']
      if direction[0] == 'down'
        return [v, direction[1] == 'left']
      if direction[0] == 'left'
        return [v, direction[1] == 'up']
      if direction[0] == 'right'
        return [v, direction[1] == 'down']
    else
      return null
  else
    return null

table.addEventListener("pointerdown", (e)->
  if not game_completed and not in_demo
    is_sliding = true
    slided_cells = [get_cell(e.target)]
)
table.addEventListener("pointermove", (e)->
  if is_sliding
    cell = get_cell(document.elementFromPoint(e.clientX, e.clientY))
    if cell
      if slided_cells.indexOf(cell) >= 0
        slided_cells = slided_cells.filter((c)-> c != cell)
        slided_cells.push(cell)
      else
        slided_cells.push(cell)
        slided_cells = slided_cells.slice(-3)
        if validate()
          node_and_direction = get_node_and_direction()
          if node_and_direction != null
            if node_and_direction
              value = node_and_direction[0]
              cw = node_and_direction[1]
              node = active_nodes_dom.filter((n)-> n.getAttribute('data-value') == "#{value}" and n.getAttribute(if cw then 'data-cw' else 'data-ccw') == "true")[0]
              if node
                row = parseInt(node.getAttribute('data-row'))
                col = parseInt(node.getAttribute('data-col'))
                animate(value, row, col, cw)
            is_sliding = false
            slided_cells = []
        else
          is_sliding = false
          slided_cells = []
)
table.addEventListener("pointerup pointerleave pointercancel", ->
  is_sliding = false
  slided_cells = []
)

document.addEventListener('keydown', (e)->
  if e.metaKey or e.ctrlKey
    if e.key == 'x' or e.key == 'X'
      if not restart_button.getAttribute('disabled')
        restart_button.click()

    if e.key == 'z' or e.key == 'Z'
      if not undo_button.getAttribute('disabled')
        undo_button.click()
)

document.getElementById('instructions-toggle').addEventListener('click', ->
  body = document.querySelector('.instructions-body')
  body.style.display = if body.style.display != 'block' then 'block' else 'none'
)