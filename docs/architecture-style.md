# Architecture Style

This project follows a layered (Presentation -> Domain -> Data) architecture.
Each layer depends only on the layer directly below it. The presentation
layer handles HTTP and templates, the domain layer holds business rules and
service logic, and the data layer owns persistence details (SQLite and JSON).

For the cart feature, the cart state is stored in the presentation layer
using the Flask session, while product data comes from the data layer via
the repository/service pipeline.

Reference:
https://martinfowler.com/bliki/PresentationDomainDataLayering.html