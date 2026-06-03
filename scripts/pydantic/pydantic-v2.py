from os import name  # noqa: F401

import pydantic
from typing import List, Optional

ver = pydantic.__version__  # prints install version
if ver.startswith("2."):
    print("[INFO] Pydantic version 2.x is installed.")
else:
    raise ImportError(
        "Pydantic version 2.x is required. Please upgrade your pydantic version."
    )


class User(pydantic.BaseModel):
    id: int
    name: str = "John Doe"  # noqa: F811


user = User(id="123")  # create an instance of User with only id

print(user.id)

print(user.model_fields_set)  # prints the fields that were set during initialization
user2 = User(id=456, name="Alice")  # create another instance of User with id and name
print(
    user2.model_fields_set
)  # prints the fields that were set during initialization for user2

print(user.model_dump())  # prints the dictionary representation of the user instance
print(user.model_dump_json())  # prints the JSON representation of the user instance
print(user.model_json_schema())  # prints the JSON schema of the User model


class Food(pydantic.BaseModel):
    name: str
    price: float
    ingredients: Optional[List[str]] = (
        None  # set default value to None for optional field
    )


class Restaurant(pydantic.BaseModel):
    name: str
    location: str
    foods: List[
        Food
    ]  # list of Food items in the restaurant's menu, uses Food model as the type for the items in the list


restaurant = Restaurant(
    name="Subshop",
    location="123 Main St",
    foods=[
        Food(
            name="Burger", price=9.99, ingredients=["Bun", "Patty", "Lettuce", "Tomato"]
        ),
        Food(
            name="Pizza",
            price=14.99,
            ingredients=["Dough", "Tomato Sauce", "Cheese", "Pepperoni"],
        ),
        Food(name="Salad", price=7.99),
    ],
)

for food in restaurant.foods:
    print(f"Food: {food.name}, Price: £{food.price}")
print(restaurant.model_dump())

print(
    restaurant.foods[2].ingredients
)  # prints None since ingredients is optional and not provided for the Salad food item

from pydantic import EmailStr, PositiveInt, conlist, Field, HttpUrl  # noqa: E402


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
    email: EmailStr  # validates that the email is in a proper format


class Restaurant(pydantic.BaseModel):
    name: str = Field(..., pattern=r"^[a-zA-Z0-9-' ]+$")  # noqa: F811
    address: Address  # nested model for the restaurant's address
    employees: conlist(
        Employee, min_length=2
    )  # list of Employee items with a minimum of 2 employees required, uses Employee model as the type for the items in the list
    number_of_seats: (
        PositiveInt  # validates that the number of seats is a positive integer
    )
    owner: Owner  # nested model for the restaurant's owner
    website: Optional[HttpUrl] = (
        None  # optional field for the restaurant's website URL, validated as a proper URL format
    )


newRestaurant = Restaurant(
    name="Gourmet Haven",
    address=Address(
        street="456 Elm St", city="Springfield", state="IL", zip_code="62704"
    ),
    employees=[
        Employee(name="Alice Smith", email="alice@smith.com", position="Chef"),
        Employee(name="Bob Johnson", email="bob@johnson.com", position="Manager"),
    ],
    number_of_seats=50,
    owner=Owner(name="Charlie Brown", email="charlie@peanuts.com"),
    website="https://www.gourmethaven.com",
)

print(
    newRestaurant.address.city + ", " + newRestaurant.address.state
)  # prints the city and state from the nested Address model
employee_names = [
    employee.name for employee in newRestaurant.employees
]  # creates a list of employee names from the nested Employee models
first_names = [name.split()[0] for name in employee_names]  # noqa: F811
last_names = [
    employee.name.split()[-1] for employee in newRestaurant.employees
]  # creates a list of the last names of employees
print(" \n".join(first_names))  # prints the list of the first names of employee
print(" \n".join(last_names))  # prints the list of the last names of employee
print(newRestaurant.owner.email)  # prints the email of the owner
