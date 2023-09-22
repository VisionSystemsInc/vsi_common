function lstrip(str)
{
  strip = match(str, /[^ ]/)
  return substr(str, strip)
}

function max(a, b)
{
  if ( a > b )
    return a
  return b
}

function get_path()
{
  result=""
  sep="" # Make it so the first key doesn't have a period before it
  for (join_i = 0; join_i < path_depth; ++join_i)
  {
    if (sequence_indexes[join_i] != -1)
    {
      result = result"["sequence_indexes[join_i]"]"
    }
    if (paths[join_i] != "\"\"" )
    {
      result = result sep paths[join_i]
      # Make addition keys separated by a period
      sep="."
    }
  }

  return result
}

function process_sequence(is_sequence, key, indents, paths, sequence_indexes)
{
  if ( is_sequence )
  {
    sequence_indexes[path_depth-1]++

    if ( key != "\"\"" )
    {
      # indent += 2
      indents[path_depth] = indent
      paths[path_depth] = key
      sequence_indexes[path_depth] = -1
      ++path_depth
    }
  }
  else
    sequence_indexes[path_depth-1] = -1
}

function get_indent(str)
{
  match(str, /^ */)
  return RLENGTH
}

function process_line(str)
{
  #### Parse line ####
  # Calculate the amount of indent on the current line ✅
  indent = get_indent(str)
  # 0 no match, 1 match ✅
  is_sequence = match(str, /^ *- */)

  if (is_sequence)
  {
    indent += 2 # ✅
  }

  # Splint the line into key and the remainder after the colon ✅
  remain = substr(str, 1+max(RLENGTH, indent))
  key = match(remain, /^[^ '":]+ *: */)
  if ( key )
  {
    tmp = RLENGTH
    match(remain, / *: */)
    key = substr(remain, 1, tmp-RLENGTH)
    remain = substr(remain, tmp+1)
  }
  else
    key = "\"\""

  #### Process line ####

  # Unindenting - Remove (now) unused paths from the stack
  if ( indent < last_indent )
  {
    # Add sequence, because in the sequence case, it's > not >=
    while ( path_depth && indents[path_depth-1] > indent) # + is_sequence )
    {
      delete indents[path_depth-1] # remove?
      delete paths[path_depth-1] # remove?
      delete sequence_indexes[path_depth-1] # remove?
      --path_depth
    }
    last_indent = indent
  }

  # Indenting
  if ( indent > last_indent )
  {
    indents[path_depth] = indent
    paths[path_depth] = key
    if (is_sequence)
    {
      sequence_indexes[path_depth] = sequence_indexes[path_depth-1]+1
    }
    else
      sequence_indexes[path_depth] = -1
    ++path_depth

    # process_sequence(is_sequence, key, indents, paths, sequence_indexes)
  } # Same indent
  else if (indent == last_indent )
  {
    # Corner case to handle the root node
    if ( path_depth == 0)
    {
      paths[0] = ""
      sequence_indexes[0] = -1
      indents[0] = 0
      path_depth = 1
    }

    paths[path_depth-1] = key
    if (is_sequence)
    {
      sequence_indexes[path_depth-1]++
    }
    # process_sequence(is_sequence, key, indents, paths, sequence_indexes)
  }
  last_indent = indent
}

function print_line()
{
  if (remain == "")
    print get_path(), "="
  else
    print get_path(), "=", remain
}

function pre_process_line()
{
  # Add compatibility for handling Windows line endings on Linux
  # (Still works in Windows with \r removed)
  if (length($0) && substr($0, length($0)) == "\r" )
    $0 = substr($0, 1, length($0)-1)

  # Handle multiline output from docker compose config
  while (match($0, /\\$/))
  {
    $0 = substr($0, 1, length($0)-1)
    getline line
    line = lstrip(line)
    $0 = $0 line
  }

  # Skip blank lines and comment lines (This doesn't include comments after
  # valid yaml... That's harder to parse validly in awk :-P
  if ($0 ~ /^ *($|#)/)
  {
    return 1
  }

  # The idea was to:
  # 1) detect a multiline
  # 2) getline
  # 3) store indent as multiline indent
  # 4) add everything after intent to value
  # 5) getline
  #    - check if indent is greater than or equal to
  #    - remove multiline indent spaces
  #    - Add \n + rest to value
  #    - (blank lines count as new lines)
  #    - Repeat until indent is less than multiline indent
  #    - Process line, then take the line that was just read that wasn't part
  #      of the multiline, and start the main awk loop all over again with that
  #      value. This part is try, since I can only do next in the main loop

  # However... docker compose parses this for you, so there's no need to do
  # this anymore :)

  # Detect multiline (|)
  # if (match($0, /^[^#|'"]*\| *($|#)/))
  # {
  #   print "MULTILINE"
  # }
  # if (match($0, /^[^#|'"]*> *($|#)/))
  # {
  #   1
  # }

  # Doesn't handle # comment, since they might be quoted, and I just don't want
  # to deal with that

  return 0
}

BEGIN {
  # Initialize empty arrays
  # Stores the individual parts of the yaml path
  delete paths[0]
  # How much an an indent each path detph has
  delete indents[0]
  # The index in a sequence. -1 is not a sequence, then 0, 1, ... for an sequence
  delete sequence_indexes[0]
  # Tracks length of theses three arrays
  path_depth = 0

  # Indent of the last line
  last_indent = 0
}

# Main
{
  if (pre_process_line())
    next
  process_line($0)


print "remainder: " remain | "cat 1>&2"
print "key: " key | "cat 1>&2"
print "indent: " indent | "cat 1>&2"
print "is_sequence: " is_sequence | "cat 1>&2"

for (join_i = 0; join_i < path_depth; ++join_i)
{
  print sequence_indexes[join_i] "|" paths[join_i] "|" indents[join_i] | "cat 1>&2"
}
print "---" | "cat 1>&2"

  print_line()
}