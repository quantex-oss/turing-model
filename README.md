## Overview

Turing_models is a python-based library that is currently in beta version. It covers the following functionality:

* Valuation and risk models for a wide range of equity, FX, interest rate and credit derivatives.

Although it is written entirely in Python, it can achieve speeds comparable to C++ by using Numba. As a result the user has both the ability to examine the underlying code and the ability to perform pricing and risk at speeds which compare to a library written in C++.

Users should have a good, but not advanced, understanding of Python. In terms of Python, the style of the library has been determined subject to the following criteria:

1. To make the code as simple as possible so that those with a basic Python fluency can understand and check the code.
2. To keep all the code in Python so users can look through the code to the lowest level.
3. To offset the performance impact of (2) by leveraging Numba to make the code as fast as possible without resorting to Cython.
4. To make the design product-based rather than model-based so someone wanting to price a specific product can easily find that without having to worry too much about the model – just use the default – unless they want to. For most products, a Monte-Carlo implementation has been provided both as a reference for testing and as a way to better understand how the product functions in terms of payments, their timings and conditions.
5. To make the library as complete as possible so a user can find all their required finance-related functionality in one place. This is better for the user as they only have to learn one interface.
6. To avoid complex designs. Limited inheritance unless it allows for significant code reuse. Some code duplication is OK, at least temporarily.
7. To have good documentation and easy-to-follow examples.
8. To make it easy for interested parties to contribute.

In many cases the valuations should be close to if not identical to those produced by financial systems such as Bloomberg. However for some products, larger value differences may arise due to differences in date generation and interpolation schemes. Over time it is hoped to reduce the size of such differences.


## The Library Design

The underlying Python library is split into a number of major modules:

* utilities These are utility functions used to assist you with modelling a security. These include dates (TuringDate), calendars, schedule generation, some finance-related mathematics functions and some helper functions.
* Market - These are modules that capture the market information used to value a security. These include interest rate and credit curves, volatility surfaces and prices.
* Models - These are the low-level models used to value derivative securities ranging from Black-Scholes to complex stochastic volatility models.
* Products - These are the actual securities and range from Government bonds to Bermudan swaptions.

Any product valuation is the result of the following data design:

**VALUATION** = **PRODUCT** + **MODEL** + **MARKET**

The interface to each product has a value() function that will take a model and market to produce a price.

## Dependencies

Turing_models depends on Numpy, Numba, Scipy and basic python libraries such as os, sys and datetime.

## Changelog

See the changelog for a detailed history of changes.

## Thanks

Thanks for Dominic O'Kane's financepy library.
The address of the project is https://github.com/domokane/FinancePy.git.


## License

 GPL-3.0 License - See the license file in this folder for details.