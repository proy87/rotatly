visit_time = new Date()
start_time = visit_time
end_time = start_time

board = document.getElementById('game-container')
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
shareable_text_dom = document.getElementById('shareable-text')
puzzle_date_dom = document.getElementById('puzzle-date')
today_date = null
if puzzle_date_dom
  min_date = puzzle_date_dom.getAttribute('min')
  max_date = puzzle_date_dom.getAttribute('max')
  today_date = puzzle_date_dom.value
  puzzle_date_dom.addEventListener("change", ->
    value = this.value
    if value and /^\d{4}-\d{2}-\d{2}$/.test(value) and min_date <= value <= max_date
      window.location.href = "/#{value}/"
  )

hold_timer = null
hold_duration = 500

is_sliding = false
slided_cells = []

is_rotate_node = (node)->
  return node.getAttribute('data-name') == 'rotate'

get_cells_from_indices = (indices) ->
  cells = []
  for index in indices
    row = Math.floor(index / M)
    col = index % M
    cells.push(document.getElementById("cell-#{row}-#{col}"))
  return cells

get_source_indices = (node, direct)->
  arr = node.getAttribute("data-#{if direct then 'source' else 'target'}").split(',')
  return arr.map((item) ->
    parseInt(item))

get_target_indices = (node, direct)->
  arr = node.getAttribute("data-#{if direct then 'target' else 'source'}").split(',')
  return arr.map((item) ->
    parseInt(item))

get_source_cells = (node, direct) ->
  return get_cells_from_indices(get_source_indices(node, direct))

get_target_cells = (node, direct) ->
  return get_cells_from_indices(get_target_indices(node, direct))

rotate = (node, direct)->
  htmls = []
  classes = []
  values = []
  for cell in get_source_cells(node, direct)
    htmls.push(cell.innerHTML)
    classes.push(cell.className)
    values.push(cell.getAttribute('data-value'))

  for cell, i in get_target_cells(node, direct)
    cell.innerHTML = htmls[i]
    cell.className = classes[i]
    cell.setAttribute('data-value', values[i])

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

set_shareable_text = ->
  moves_made = moves.length
  emoji = null
  text = null
  full_text = null
  rows = null

  number = "##{game_index}"
  if today_date
    number += " (#{today_date})"

  if check()
    if moves_made == moves_min_num
      emoji = '🧠✨'
      text = 'Perfect Solve'
    else if moves_made - moves_min_num <= 3
      emoji = '🤏'
      text = 'So close!'
    else
      emoji = '🧩'
      text = 'Solved'
    full_text = "Rotatly #{number} #{emoji}\n#{text}\nMoves: #{moves_made}/#{moves_min_num}\n#{canonical_url}"
  else
    moves_text = ''
    if moves_made == 0
      emoji = '😴'
      moves_text = "Didn't try today\nIt's never too late to start!"
    else if moves_made < moves_min_num * 2
      emoji = '⏳'
      moves_text = "Rotating…\nMoves: #{moves_made}"
    else
      emoji = '😤'
      moves_text = "This one got me\nWant to take a shot?"

    full_text = "Rotatly #{number} #{emoji}\n#{moves_text}\n#{canonical_url}"

  shareable_text_dom.value = full_text

set_shareable_text()

animate = (node, direct, undo = false, demo = false, callback = null) ->
  if in_animation
    return
  in_animation = true
  animated = true
  finished = 0
  cells = get_target_cells(node, true)
  node_name = node.getAttribute('data-name')
  if is_rotate_node(node)
    classes = [(if direct then 'move-right' else 'move-down'), (if direct then 'move-down' else 'move-left'),
      (if direct then 'move-left' else 'move-up'), (if direct then 'move-up' else 'move-right')]
  else if node_name == 'horizontal'
    classes = ((if direct then 'move-right' else 'move-left') for i in [0...cells.length])
  else if node_name == 'vertical'
    classes = ((if direct then 'move-down' else 'move-up') for i in [0...cells.length])

  transition_callback = (e)->
    if e.propertyName == 'transform'
      finished += 1
      if finished == cells.length
        for c, idx in cells
          c.classList.remove('animate')
          c.classList.add('non-animate')
          c.removeEventListener('transitionend', transition_callback)
          c.classList.remove(classes[idx])
        for c in cells
          c.offsetHeight
        rotate(node, direct)
        if not undo
          symbol = node.getAttribute("data#{if direct then '' else '-reverse'}-symbol")
          moves.push("#{node.getAttribute('data-index')}#{symbol}")
          moves_sequence_dom.innerHTML = if moves.length then moves.join(' ') else 'no moves'
          if not demo
            undo_button.removeAttribute('disabled')
            restart_button.removeAttribute('disabled')

        number_of_moves = moves.length
        set_shareable_text()
        if number_of_moves == 1 and not undo
          start_time = new Date()
        moves_made_num_dom.innerHTML = number_of_moves
        solved = check()
        if not demo and (number_of_moves >= moves_max_num or solved)
          end_time = new Date()
          game_completed = true
          active_nodes_dom.forEach((node)->
            window.hide_element(node)
          )
          window.hide_element(undo_button)
          if solved
            one_less_move_dom.innerHTML = number_of_moves - 1
            moves_num_dom.innerHTML = number_of_moves
            block = document.getElementById("#{if number_of_moves > moves_min_num then 'non-' else ''}min-text")
          else
            block = document.getElementById("non-solve-text")
          #window.show_element(block)

          window.send_request(track_url, {
            game_index: game_index, init_time: (start_time - visit_time) / 1000,
            game_time: (end_time - start_time) / 1000, moves: moves.join(''), length: number_of_moves
          })

        in_animation = false

        if callback
          callback()

  for cell, idx in cells
    cell.classList.remove('non-animate')
    cell.classList.add('animate')
    cell.addEventListener('transitionend', transition_callback)
    cell.classList.add(classes[idx])


undo = (callback)->
  if moves.length > 0
    elem = moves.pop()
    moves_sequence_dom.innerHTML = if moves.length then moves.join(' ') else 'no moves'
    index = elem.slice(0, -1)
    direction = elem.slice(-1)
    node = active_nodes_dom.filter((n)->
      if n.getAttribute('data-index') == "#{index}"
        if n.getAttribute('data-symbol') == direction or n.getAttribute('data-reverse-symbol') == direction
          return true
    )[0]
    if node
      animate(node, direction != node.getAttribute('data-symbol'), true, false, if callback then callback else undo)

make_move = ->
  setTimeout(->
    if pre_moves.length > 0
      undo_button.setAttribute('disabled', true)
      restart_button.setAttribute('disabled', true)
      elem = pre_moves.shift()
      index = elem[0]
      direction = elem[1]
      node = active_nodes_dom.filter((n)->
        if n.getAttribute('data-index') == "#{index}"
          if n.getAttribute('data-symbol') == direction and n.getAttribute('data-allow-direct') == 'true'
            return true
          if n.getAttribute('data-reverse-symbol') == direction and n.getAttribute('data-allow-reverse') == 'true'
            return true
      )[0]
      if node
        animate(node, direction == node.getAttribute('data-symbol'), false, true, make_move)
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

active_nodes_dom.filter((n)-> is_rotate_node(n)).forEach((node)->
  node.addEventListener('click', ->
    if not animated
      animate(this, true)
  )
  node.addEventListener('pointerdown', ->
    n = this
    if not in_animation
      animated = false
      hold_timer = setTimeout(->
        clearTimeout(hold_timer)
        hold_timer = null
        if not animated
          animate(n, false)
      , hold_duration
      )
  )
  node.addEventListener('pointerup pointerleave pointercancel', ->
    if hold_timer
      clearTimeout(hold_timer)
      hold_timer = null
  )
)

active_nodes_dom.filter((n)-> not is_rotate_node(n)).forEach((node)->
  node.addEventListener('click', ->
    animate(this, node.getAttribute('data-direction') == node.getAttribute('data-symbol'))
  )
)

document.addEventListener('contextmenu', (evt)->
  node = evt.target
  if board.contains(node)
    evt.preventDefault()
    if not animated and is_rotate_node(node) and active_nodes_dom.includes(node)
      animate(node, false)
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
    window.hide_element(node)
  )
  active_nodes_dom.forEach((node)-> window.show_element(node))
  undo_button.setAttribute('disabled', true)
  window.show_element(undo_button)
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
  if slided_cells.length != 3
    return null

  indices = []
  for cell in slided_cells
    row = parseInt(cell.getAttribute('data-row'))
    col = parseInt(cell.getAttribute('data-col'))
    indices.push(row * M + col)

  indices_str = indices.join(',')
  for node in active_nodes_dom
    node_indices = get_target_indices(node, true)
    node_indices = node_indices.concat(node_indices)
    if node_indices.join(',').includes(indices_str)
      return [node, true]

    node_indices.reverse()
    if node_indices.join(',').includes(indices_str)
      return [node, false]


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
              node = node_and_direction[0]
              direct = node_and_direction[1]
              if node and node.getAttribute("data-allow-#{if direct then 'direct' else 'reverse'}") == 'true'
                animate(node, direct)
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

document.getElementById('copy-result').addEventListener('click', ->
  share_text = shareable_text_dom.value
  navigator.clipboard.writeText(share_text).then(->
    toast = document.getElementById('copy-toast')
    window.show_element(toast)
    setTimeout(->
      window.hide_element(toast)
    , 2000)
  )
  window.send_request(track_url, {
      game_index: game_index,
      init_time: (start_time - visit_time) / 1000,
      game_time: (end_time - start_time) / 1000,
      moves: moves.join(''),
      length: moves.length,
      copied: true,
    }
  )
)

document.getElementById('share-icon').addEventListener('click', ->
  container = document.getElementById('share-container')
  container.parentNode.insertBefore(container, document.getElementById('target-outline-container'))
  container.insertBefore(shareable_text_dom, document.getElementById('copy-result'))
)