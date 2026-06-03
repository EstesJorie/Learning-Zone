# Pydantic V2

Pydantic allows for "strict typing" by using *type annotations*, allowing for clear and secure data models. This guide is for Pydantic v2+, the code snippet below ensures that this version is installed, and raises an import error if not.

```python
import pydantic

ver = pydantic.__version__
if ver.startswith("2."):
    print("Pydantic version 2.x is installed.")
else:
    raise ImportError("Pydantic version 2.x is required. Please upgrade your pydantic version.")
```

## Basics

To start we need to import the `Base Model` from Pydantic.

```python
class User(pydantic.BaseModel):
    id: int
    name: str = "John Doe"
```

The `BaseModel` is a class which is used to define data structures and validate information, therefore by creating a class which inherits from this base we ensure that our data automatically adheres to our specifications.

In the above example, we have created the `User` class with an id of type `int` which means if we instantiate this `User` class as follows:

```python
user = User(id=123)
```

We will get no errors. But, if we were to pass a `str` for the id then we will get the following error:

```bash
pydantic_core._pydantic_core.ValidationError: 1 validation error for User
id
  Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='abcd', input_type=str]
    For further information visit https://errors.pydantic.dev/2.13/v/int_parsing
```

### Model Fields Set

The method `model_fields_set` is a helper method provided in Pydantic that allows us to analyse properties of our models, this method will print the fields that were set during the initalisation of this model object.

```python
print(user.model_fields_set)

# {'id'}
```

Here, the model_fields_set is only showing the `id` field as it was the only parameter that we set during creation of this `User` model object despite the fact the `User` class has a default value for the `name` attribute.

### Model Dump

Another set of helper methods we have in Pydantic are the model dump methods. These convert a class instance to various formats.

```python
print(user.model_dump()) # dictionary representation of the user instance
print(user.model_dump_json()) # JSON representation of the user instance
print(user.model_json_schema()) # JSON schema of the User model

# {'id': 123, 'name': 'John Doe'}
# {"id":123,"name":"John Doe"}
# {'properties': {'id': {'title': 'Id', 'type': 'integer'}, 'name': {'default': 'John Doe', 'title': 'Name', 'type': 'string'}}, 'required': ['id'], 'title': 'User', 'type': 'object'}
```

## Nested Models

We can also nest models as the type for a particular attribute in another model:

```python
from typing import List, Optional

class Food(pydantic.BaseModel):
    name: str
    price: float
    ingredients: Optional[List[str]] = None

class Restaurant(pydantic.BaseModel):
    name: str
    location: str
    foods: List[Food]
```

Here, the Restaurant model uses the Food model for its `foods` attribute. We can then create an instance of this Restaurant model:

```python
restaurant = Restaurant(
    name="Subshop",
    location="123 Main St",
    foods=[
        Food(name="Burger", price=9.99, ingredients=["Bun", "Patty", "Lettuce", "Tomato"]),
        Food(name="Pizza", price=14.99, ingredients=["Dough", "Tomato Sauce", "Cheese", "Pepperoni"]),
        Food(name="Salad", price=7.99)
    ]
)

for food in restaurant.foods:
    print(f"Food: {food.name}, Price: £{food.price}")

# Food: Burger, Price: $9.99
# Food: Pizza, Price: $14.99
# Food: Salad, Price: $7.99
```

In the example above, we are looping through all of the foods within this restaurant instance and despite the fact we did not set the ingredients for the ***Salad*** everything ran successfully. This is because we set the `ingredients` attribute to be optional. We can verify this behaviour like so:

```python
print(restaurant.foods[2].ingredients)

# None
```

## Advanced Data Types

Pydantic also provides more advanced, optional data types which we can use in our models. One such example is *email*. To install this you'll need to explicitly add it:

```bash
pip install 'pydantic[email]'
```

Below is an example using some of these classes:

```python
from pydantic import EmailStr, PositiveInt, conlist, Field, HttpUrl

class Address(pydantic.BaseModel):
    street: str
    city: str
    state: str
    zip_code: str

class Employee(pydantic.BaseModel):
    name: str
    email: EmailStr  # validates that the email is in a proper format
    position: str

class Owner(pydantic.BaseModel):
    name: str
    email: EmailStr

class Restaurant(pydantic.BaseModel):
    name: str = Field(..., pattern=r"^[a-zA-Z0-9-' ]+$")
    address: Address
    employees: conlist(Employee, min_length=2)  # list of Employee items with a minimum of 2 employees
    number_of_seats: PositiveInt  # validates that the number of seats is a positive integer
    owner: Owner
    website: Optional[HttpUrl] = None

newRestaurant = Restaurant(
    name="Gourmet Haven",
    address=Address(
        street="456 Elm St",
        city="Springfield",
        state="IL",
        zip_code="62704"
    ),
    employees=[
        Employee(name="Alice Smith", email="alice@smith.com", position="Chef"),
        Employee(name="Bob Johnson", email="bob@johnson.com", position="Manager")
    ],
    number_of_seats=50,
    owner=Owner(name="Charlie Brown", email="charlie@peanuts.com"),
    website="https://www.gourmethaven.com"
)
```
