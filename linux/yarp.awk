function max(a, b)
{
  if ( a > b )
    return a
  return b
}

function join(array, sep)
{
  # print length(array)
  if (!length(array))
    return
  result = array[0]
# for ( q in array )
#   print q
  for (join_i = 1; join_i < length(array); ++join_i)
  {
    assert(join_i < 100, "Ah shit")
    result = result sep array[join_i]
  }
  # print length(array)
  return result
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

BEGIN {
  # Initialize empty arrays
  delete paths[0]
  delete indents[0]
  delete sequences[0]

  last_indent = 0
}

{
  if ($0 ~ /^ *$/)
    next

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

  # # Count the - as an indent
  # indent = indent + sequence*2
  #### Process line ####

  # No support for multiline (|)

  # Unindenting
  if ( indent < last_indent )
  {
    # Add sequence, because in the sequence case, it's > not >=
    while ( length(indents) && indents[length(indents)-1] >= indent + sequence )
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
    if ( sequence )
    {
      paths[length(paths)] = ""
      sequences[length(sequences)] = 0

      if ( key != "\"\"" )
      {
        indent += 2
        indents[length(indents)] = indent
        paths[length(paths)] = key
        sequences[length(sequences)] = -1
      }
    }
    else
    {
      paths[length(paths)] = key
      sequences[length(sequences)] = -1
    }
  } # Same indent
  else if (indent == last_indent )
  {
    # Corner case
    if ( length(paths) == 0)
    {
      paths[0]
      sequences[0]=-1
      indents[0]=0
    }

    if ( sequence )
    {
      sequences[length(sequences)-1]++
      # paths[length(paths)-1] = "["sequences[length(sequences)-1]"]"

      if ( key != "\"\"" )
      {
        indent += 2
        indents[length(indents)] = indent
        paths[length(paths)] = key
        sequences[length(sequences)] = -1
      }
    }
    else
      paths[length(paths)-1] = key
  }
  last_indent = indent

  print get_path(), "=", remain
  # print indent, sequence, key, remain
}

END {
  if (_assert_exit)
    exit 1
  # print join(q, ".")
  # print(length(q))
  # for (x in q)
  #   print x":"q[x]
}