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
  result = array[0]
  for (i = 1; i < length(array); i++)
  {
    result = result sep array[i]
  }
  return result
}

BEGIN {
  delete path[0]
  delete indents[0]

  last_indent = -1
}

{
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

  # No support for array (-) yet or multiline (|)
  if ( indent < last_indent )
  {
    for (i = length(indents)-1; i>=0; i++)
    {
      if ( indent < indents[i] )
      {
        delete indents[i]
        delete path[i]
      }
      else
        break
    }
    last_indent = indent
  }

  if ( indent > last_indent )
  {
    indents[length(indents)] = indent
    if ( sequence )
    {
      path[length(path)] = "[0]"
    }
    else
    {
      path[length(path)] = key
    }
  }
  else if (indent == last_indent )
  {
    path[length(path)-1] = key
  }
  else
  {

  }
  last_indent = indent

  print join(path, "."), "=", remain
  # print indent, sequence, key
  # print remain
}

END {
  # print join(q, ".")
  # print(length(q))
  # for (x in q)
  #   print x":"q[x]
}