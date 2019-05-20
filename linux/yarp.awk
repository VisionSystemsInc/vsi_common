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
  delete path[0]
  delete indents[0]
  delete sequences[0]

  last_indent = 0
}

{
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

  # Count the - as an indent of 2, since the space after the - is required
  indent = indent + sequence * 2
  #### Process line ####

  # No support for multiline (|)

  print indent

  # Unindenting
  if ( indent < last_indent )
  {
    while ( length(indents) && indents[length(indents)-1] >= indent )
    {
      delete indents[length(indents)-1]
      delete path[length(path)-1]
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
      path[length(path)] = "[0]"
      sequences[length(sequences)] = 0

      if ( key != "\"\"" )
      {
        last_indent = indent
        indents[length(indents)] = indent
        path[length(path)] = key
        sequences[length(sequences)] = -1
      }
    }
    else
    {
      path[length(path)] = key
      sequences[length(sequences)] = -1
    }
  } # Same indent
  else if (indent == last_indent )
  {
    # Corner case
    if ( length(path) == 0)
    {
      path[0]
      sequences[0]=0
      indents[0]
    }

    if ( sequence )
    {
      print "-===-"
      sequences[length(sequences)-1]++
      path[length(path)-1] = "["sequences[length(sequences)-1]"]"
    }
    else
      path[length(path)-1] = key
  }
  last_indent = indent

  print join(path, "."), "=", remain
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