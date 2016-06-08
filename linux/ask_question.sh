#!/usr/bin/env false 
#MEANT to be sourced!!!!

#Pretty version of ask Y/N with optional default value
function ask_question()
{ #(question) (optional default)
  if [[ $# > 2 ]]; then
    local default_response="$3"
  else
    local default_response=
  fi

  #Check to see if the variable already has been set. This way the input is 
  #skipped. This is great for automating ask_question
  if [ "${!2=}" != "" ]; then
    local override=${!2}
  fi

  while true; do
    #Prompt user
    if [ "${override=}" != "" ]; then
      echo "$1 ${!2}"
      ans=$override
      override="" #Prevent infinite loop
    elif [ "$default_response" == "" ]; then
      read -r -p "$1 " ans
    else
      read -r -p "$1 ($default_response) " ans
    fi

    #Replace with default
    if [ "$ans" == "" ]; then
      ans="$default_response"
    fi

    #Check answers
    case $ans in
      [Yy]* ) eval $2=1; break;;
      [Nn]* ) eval $2=0; break;;
      * ) echo "Please answer yes or no (y/n)";;
    esac
  done
}