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
  for (join_i = 0; join_i < length_sequences; ++join_i)
  {
    if (sequences[join_i] != -1)
    {
      result = result"["sequences[join_i]"]"
    }
    else if (paths[join_i] != "" )
    {
      result = result sep paths[join_i]
      # Make addition keys separated by a period
      sep="."
    }
  }

  return result
}

function process_sequence(sequence, key, indents, paths, sequences)
{
  if ( sequence )
  {
    sequences[length_sequences-1]++

    if ( key != "\"\"" )
    {
      indent += 2
      indents[length_sequences] = indent
      paths[length_sequences] = key
      sequences[length_sequences] = -1
      ++length_sequences
    }
  }
  else
    sequences[length_sequences-1] = -1
}

function get_indent(str)
{
  match(str, /^ */)
  return RLENGTH
}

function process_line(str)
{
  #### Parse line ####
  indent = get_indent(str)
  # 0 no match, 1 match
  sequence = match(str, /^ *- */)
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

  # Unindenting
  if ( indent < last_indent )
  {
    # Add sequence, because in the sequence case, it's > not >=
    while ( length_sequences && indents[length_sequences-1] > indent) # + sequence )
    {
      delete indents[length_sequences-1]
      delete paths[length_sequences-1]
      delete sequences[length_sequences-1]
      --length_sequences
    }
    last_indent = indent
  }

  # Indenting
  if ( indent > last_indent )
  {
    indents[length_sequences] = indent
    paths[length_sequences] = key
    sequences[length_sequences] = -1
    ++length_sequences

    process_sequence(sequence, key, indents, paths, sequences)
  } # Same indent
  else if (indent == last_indent )
  {
    # Corner case
    if ( length_sequences == 0)
    {
      paths[0] = ""
      sequences[0] = -1
      indents[0] = 0
      length_sequences = 1
    }

    paths[length_sequences-1] = key

    process_sequence(sequence, key, indents, paths, sequences)
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
    $0 = substr($0, 0, length($0)-1)

  # Handle multiline output from docker-compose config
  while (match($0, /\\$/))
  {
    $0 = substr($0, 0, length($0)-1)
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

  # However... docker-compose parses this for you, so there's no need to do
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
  delete paths[0]
  delete indents[0]
  delete sequences[0]

  length_sequences = 0

  last_indent = 0
}

# Main
{
  if (pre_process_line())
    next
  process_line($0)
  print_line()
}