#! /opt/homebrew/bin/php

<?php
// Making sure the contexts column in the requirements file can be parsed correctly in php.
$file = fopen("course_mapper.requirements.csv","r");
while ($row = fgetcsv($file))
{
  echo("\n${row[4]}\n");
  print_r(json_decode($row[4]));
}
fclose($file);
?>