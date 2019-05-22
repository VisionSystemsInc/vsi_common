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
  for (join_i = 0; join_i < length(indents); ++join_i)
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

function pa(array)
{
  print "----"
  for (xx in array)
    print "["xx"]"array[xx]
  print "---"
}

function assert(condition, string)
{
  if (! condition) {
    printf("%s:%d: assertion failed: %s\n", FILENAME, FNR, string) > "/dev/stderr"
    _assert_exit = 1
    exit 1
  }
}

function process_sequence(sequence, key, indents, paths, sequences)
{
  if ( sequence )
  {
    sequences[length(sequences)-1]++

    if ( key != "\"\"" )
    {
      indent += 2
      indents[length(indents)] = indent
      paths[length(paths)] = key
      sequences[length(sequences)] = -1
    }
  }
  else
    sequences[length(sequences)-1] = -1
}

BEGIN {
  # Initialize empty arrays
  delete paths[0]
  delete indents[0]
  delete sequences[0]

  last_indent = 0
}

{
  # Skip blank lines
  if ($0 ~ /^[ #]*$/)
    next

  # Handle multiline output from docker-compose config
  while (match($0, /\\$/))
  {
    $0 = substr($0, 0, length($0)-1)
    getline line
    line = lstrip(line)
    $0 = $0 line
  }

  # No support for multiline (|) or (>)
  # Doesn't handle # comment, since they might be quoted, and I just don't want
  # to deal with that

  #### Parse line ####
  match($0, "^ *")
  indent = RLENGTH
  # 0 no match, 1 match
  sequence = match($0, "^ *- *")
  remain = substr($0, 1+max(RLENGTH, indent))

  key = match(remain, "^[^ '\":]+ *: *")
  if ( key )
  {
    tmp = RLENGTH
    match(remain, " *: *")
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
    while ( length(indents) && indents[length(indents)-1] > indent) # + sequence )
    {
      delete indents[length(indents)-1]
      delete paths[length(paths)-1]
      delete sequences[length(sequences)-1]
    }
    last_indent = indent
  }

  # Indenting
  if ( indent > last_indent )
  {
    indents[length(indents)] = indent
    paths[length(paths)] = key
    sequences[length(sequences)] = -1

    process_sequence(sequence, key, indents, paths, sequences)
  } # Same indent
  else if (indent == last_indent )
  {
    # Corner case
    if ( length(paths) == 0)
    {
      paths[0]=""
      sequences[0]=-1
      indents[0]=0
    }

    paths[length(paths)-1] = key

    process_sequence(sequence, key, indents, paths, sequences)
  }
  last_indent = indent

  assert(length(paths) == length(indents), "#Path != #indents")
  assert(length(paths) == length(sequences), "#Path != #sequences")

  print get_path(), "=", remain
}

END {
  if (_assert_exit)
    exit 1
}