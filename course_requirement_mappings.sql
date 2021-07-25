-- What requirements can a course satisfy?
drop table if exists program_requirements cascade;
drop table if exists course_requirement_mappings cascade;

-- Program requirements
--  The name is the name of the requirement (not the title of the program, which is in the
--  requirement_blocks table)
--  XXX_required: How many classes/credits are required
--  XXX_alternatives: Totals for all the courses that can satisfy this requirement.
--  conjunction: classes AND credits versus classes OR credits
--  The context is a list of containing requirement names, super-names, super-super-names, ...
create table program_requirements (
id serial primary key,
institution text not null,
requirement_id text not null,
requirement_name text not null,
num_courses_required text not null,
course_alternatives text not null,
conjunction text,
num_credits_required text not null,
credit_alternatives text not null,
context jsonb not null,
qualifiers jsonb not null,
foreign key (institution, requirement_id) references requirement_blocks,
unique (institution, requirement_id, requirement_name)
);

-- Map courses to program requirements.
create table course_requirement_mappings (
course_id integer,
offer_nbr integer,
program_requirement_id integer references program_requirements(id) on delete cascade,
qualifiers text default '',
foreign key (course_id, offer_nbr) references cuny_courses,
primary key (course_id, offer_nbr, program_requirement_id)
);
