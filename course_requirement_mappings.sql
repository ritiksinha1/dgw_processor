-- What requirements can a course satisfy?
drop table if exists active_courses cascade;
drop table if exists requirements cascade;
drop table if exists mappings cascade;

-- One row for each active course that has been found in any list of courses for any requirement.
-- This information is redundant to a subset of the information in cuny_curriculum.cuny_courses.
create table active_courses (
course_id integer,
offer_nbr integer,
institution text,
discipline text,
catalog_nbr text,
title text,
credits text,
primary key (course_id, offer_nbr));

-- One row for each requirement.
--  The type will always be MAJOR, CONC(ENTRATION), or MINOR
--  The value will be the name of the type (PSY-BA, CSCI-BS, etc.)
--  XXX_required: How many classes/credits are required
--  XXX_alternatives: Totals for all the courses that can satisfy this requirement.
--  The context is a '|' concatenated list of requirement names, sub-names, sub-sub-names, ...
create table requirements (
id integer primary key,
institution text,
type text,
value text,
courses_required integer,
course_alternatives integer,
credits_required real,
credit_alternatives real,
context text
);

-- For each course that satisfies a requirement tell which requirement and whether there is a
-- residency requirement.
create table mappings (
course_id integer,
offer_nbr integer,
requirement_id integer references requirements,
residency_required boolean,
foreign key (course_id, offer_nbr) references active_courses,
primary key (course_id, offer_nbr, requirement_id)
);
