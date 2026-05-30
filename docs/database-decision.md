# Database Decisions

This document records the key decisions made about the database schema and
domain model and the reasoning behind each one.

---

## Address as a Value Object

### Decision
Address fields (street, suburb, state, postcode) are modelled as a separate
Address class rather than four loose fields on Customer.

### Reasoning
An address is a real concept in the domain. It has meaning as a unit. Four
loose fields on Customer do not capture that meaning and allow partial
addresses to exist, which the database schema explicitly forbids.

By making Address its own class, the constraint that all four fields must be
provided together is structural rather than conditional. It is impossible to
create an Address with only some fields because the constructor requires all
four. A ValueError check can be forgotten or bypassed. A class constructor
cannot.

This approach also aligns with the PhysicalLocation class already in the
domain model, which applies the same principle to book shelf locations.

### Trade-off
The customer repository must flatten the Address object into four columns
when saving and reconstruct it when loading. This is handled in
src/data/repositories/customer_repository.py and is the correct place for
that concern as the data layer is responsible for mapping between domain
objects and database rows.

### Alternatives considered
A ValueError check in the Customer constructor was considered. This was
rejected because the constraint is better expressed through structure than
through runtime validation.
