-- What requirements can a course satisfy?
drop table if exists active_courses cascade;
drop table if exists requirements cascade;
drop table if exists mappings cascade;

create table active_courses (
course_id integer,
offer_nbr integer,
institution text,
discipline text,
title text,
credits text,
primary key (course_id, offer_nbr));

create table requirements (
id integer primary key,
institution text,
type text,
value text,
required_courses integer,
required_credits real,
context text
);

create table mappings (
course_id integer,
offer_nbr integer,
requirement_id integer references requirements,
foreign key (course_id, offer_nbr) references active_courses,
primary key (course_id, offer_nbr, requirement_id)
);
