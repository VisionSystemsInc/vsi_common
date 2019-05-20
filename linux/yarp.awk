function max(a, b)
{
  if ( a > b )
    return a
  return b
}

# Prints out
# Line 1
# 1 - Number of spaced indent
# 2 - is sequence?
# 3 - key name, "" for no key
# Line 2 - Value

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

function get_path()
{

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


  # remain = substr(remain, RLENGTH)
  # key = substr(key, 1, length(key))

  # anchor=match($0, "&[^ '\"]+ *$")
  # if ( anchor == 0 )
  # {
  #   anchor_name="-"
  #   anchor=0
  # }
  # else
  # {
  #   anchor_name=substr($0, anchor+1)
  #   anchor=1
  # }

  #### Process line ####

  # No support for multiline (|)
  if ( indent < last_indent )
  {

    while ( length(indents) && indents[length(indents)-1] >= indent )
    # for (i = length(indents)-1; i>=0; i++)
    {
      # print "zz"length(indents)
      # for ( q in indents )
      #   print q
      # if ( indent < indents[i] )
      # {
        delete indents[length(indents)-1]
        delete path[length(path)-1]
        delete sequences[length(sequences)-1]
      # print "yy"length(indents)
      # for ( q in indents )
      #   print q
      # }
      # else
      #   break
    }
    last_indent = indent
  }


  if ( indent > last_indent )
  {
    indents[length(indents)] = indent
    if ( sequence )
    {
      path[length(path)] = "[0]"
      sequences[length(sequences)] = 0

      if ( key != "\"\"" )
      {
        # print "i", join(indents, ",")
        # print "p", join(path, ",")
        # print "s", join(sequences, ",")

        last_indent = indent + 1
        indents[length(indents)] = indent + 1
        path[length(path)] = key
        sequences[length(sequences)] = -1
        # pa(indents)
        # print "i", join(indents, ",")
        # print "p", join(path, ",")
        # print "s", join(sequences, ",")
      }
    }
    else
    {
      path[length(path)] = key
      sequences[length(sequences)] = -1
    }
  }
  else if (indent == last_indent )
  {
    if ( length(path) == 0)
    {
      path[0]
      sequences[0]=0
      indents[0]
    }

    if ( sequence )
    {
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