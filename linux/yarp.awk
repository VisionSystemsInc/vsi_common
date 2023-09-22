# Standard left strip string
function lstrip(str)
{
  strip = match(str, /[^ ]/)
  return substr(str, strip)
}

# Standard max function
function max(a, b)
{
  if ( a > b )
    return a
  return b
}

# Turn sequence_indexes and paths into a "yaml path"
function get_path()
{
  result=""
  sep="" # Make it so the first key doesn't have a period before it
  for (join_i = 0; join_i < path_depth; ++join_i)
  {
    # If it is a sequence, add [#]. This comes before a key because a key in a
    # sequence represents a sequence of maps
    if (sequence_indexes[join_i] != -1)
    {
      result = result"["sequence_indexes[join_i]"]"
    }
    # If there is a non-empty key, display it
    if (paths[join_i] != "\"\"" )
    {
      result = result "." paths[join_i]
    }
  }

  if (match(result, "^\\."))
    result = substr(result, 2)

  return result
}

# Calculate the amount of indent
function get_indent(str)
{
  match(str, /^ */)
  indent = RLENGTH

  # 0 no match, 1 match
  is_sequence = match(str, /^ *- */)
  if (is_sequence)
  {
    # "- " counts as an indent of 2
    indent += 2
  }

  return indent
}

function process_line(str)
{
  #### Parse line ####
  # Calculate the amount of indent on the current line
  indent = get_indent(str)

  # Splint the line into key and the remainder after the colon
  remain = substr(str, 1+max(RLENGTH, indent))
  key = match(remain, /^[^ '":]+ *: */)   #"# VS Code parser error
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
    while ( path_depth && indents[path_depth-1] > indent)
    {
      # delete indents[path_depth-1]
      # delete paths[path_depth-1]
      # delete sequence_indexes[path_depth-1]
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
      if(path_depth)
        sequence_indexes[path_depth] = sequence_indexes[path_depth-1]+1
      else
        # If the top level node is a sequesnce, then sequence_indexes[-1]+1
        # would erroneously return 1 instead of 0
        sequence_indexes[path_depth] = 0
    }
    else
      # -1 means not an sequence
      sequence_indexes[path_depth] = -1
    ++path_depth
  } # Same indent
  else if (indent == last_indent )
  {
    paths[path_depth-1] = key
    if (is_sequence)
    {
      sequence_indexes[path_depth-1]++
    }
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

# Skip blank line and comment, and combine multiple line expressions
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

  # Doesn't handle varying/multiple spaces after the - in a sequence:
  # -   food: 1
  #     loot: 2
  # - good: 3

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

  # Indent of the last line. Start at -1 so that the root node trigger as the
  # first indent
  last_indent = -1
}

# Main
{
  if (pre_process_line())
    next
  process_line($0)

# # Debug for next time I need to debug this
# print "remainder: " remain | "cat 1>&2"
# print "key: " key | "cat 1>&2"
# print "indent: " indent | "cat 1>&2"
# print "is_sequence: " is_sequence | "cat 1>&2"

# for (join_i = 0; join_i < path_depth; ++join_i)
# {
#   print sequence_indexes[join_i] "|" paths[join_i] "|" indents[join_i] | "cat 1>&2"
# }
# print "---" | "cat 1>&2"

  print_line()
}