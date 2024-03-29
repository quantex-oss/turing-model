###############################################################################
# TODO: Do some timings and tidy up logic in adjustment function
###############################################################################

import datetime
from enum import Enum
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.error import TuringError

# from numba import njit, jit, int64, boolean

easterMondayDay = [98, 90, 103, 95, 114, 106, 91, 111, 102, 87,
                   107, 99, 83, 103, 95, 115, 99, 91, 111, 96, 87,
                   107, 92, 112, 103, 95, 108, 100, 91,
                   111, 96, 88, 107, 92, 112, 104, 88, 108, 100,
                   85, 104, 96, 116, 101, 92, 112, 97, 89, 108,
                   100, 85, 105, 96, 109, 101, 93, 112, 97, 89,
                   109, 93, 113, 105, 90, 109, 101, 86, 106, 97,
                   89, 102, 94, 113, 105, 90, 110, 101, 86, 106,
                   98, 110, 102, 94, 114, 98, 90, 110, 95, 86,
                   106, 91, 111, 102, 94, 107, 99, 90, 103, 95,
                   115, 106, 91, 111, 103, 87, 107, 99, 84, 103,
                   95, 115, 100, 91, 111, 96, 88, 107, 92, 112,
                   104, 95, 108, 100, 92, 111, 96, 88, 108, 92,
                   112, 104, 89, 108, 100, 85, 105, 96, 116, 101,
                   93, 112, 97, 89, 109, 100, 85, 105, 97, 109,
                   101, 93, 113, 97, 89, 109, 94, 113, 105, 90,
                   110, 101, 86, 106, 98, 89, 102, 94, 114, 105,
                   90, 110, 102, 86, 106, 98, 111, 102, 94, 114,
                   99, 90, 110, 95, 87, 106, 91, 111, 103, 94,
                   107, 99, 91, 103, 95, 115, 107, 91, 111, 103,
                   88, 108, 100, 85, 105, 96, 109, 101, 93, 112,
                   97, 89, 109, 93, 113, 105, 90, 109, 101, 86,
                   106, 97, 89, 102, 94, 113, 105, 90, 110, 101,
                   86, 106, 98, 110, 102, 94, 114, 98, 90, 110,
                   95, 86, 106, 91, 111, 102, 94, 107, 99, 90,
                   103, 95, 115, 106, 91, 111, 103, 87, 107, 99,
                   84, 103, 95, 115, 100, 91, 111, 96, 88, 107,
                   92, 112, 104, 95, 108, 100, 92, 111, 96, 88,
                   108, 92, 112, 104, 89, 108, 100, 85, 105, 96,
                   116, 101, 93, 112, 97, 89, 109, 100, 85, 105]

precomputedChinaHolidays = [TuringDate(y=2005, m=1, d=3),
                            TuringDate(y=2005, m=2, d=7),
                            TuringDate(y=2005, m=2, d=8),
                            TuringDate(y=2005, m=2, d=9),
                            TuringDate(y=2005, m=2, d=10),
                            TuringDate(y=2005, m=2, d=11),
                            TuringDate(y=2005, m=2, d=14),
                            TuringDate(y=2005, m=2, d=15),
                            TuringDate(y=2005, m=5, d=2),
                            TuringDate(y=2005, m=5, d=3),
                            TuringDate(y=2005, m=5, d=4),
                            TuringDate(y=2005, m=5, d=5),
                            TuringDate(y=2005, m=5, d=6),
                            TuringDate(y=2005, m=10, d=3),
                            TuringDate(y=2005, m=10, d=4),
                            TuringDate(y=2005, m=10, d=5),
                            TuringDate(y=2005, m=10, d=6),
                            TuringDate(y=2005, m=10, d=7),
                            TuringDate(y=2006, m=1, d=2),
                            TuringDate(y=2006, m=1, d=3),
                            TuringDate(y=2006, m=1, d=26),
                            TuringDate(y=2006, m=1, d=27),
                            TuringDate(y=2006, m=1, d=30),
                            TuringDate(y=2006, m=1, d=31),
                            TuringDate(y=2006, m=2, d=1),
                            TuringDate(y=2006, m=2, d=2),
                            TuringDate(y=2006, m=2, d=3),
                            TuringDate(y=2006, m=5, d=1),
                            TuringDate(y=2006, m=5, d=2),
                            TuringDate(y=2006, m=5, d=3),
                            TuringDate(y=2006, m=5, d=4),
                            TuringDate(y=2006, m=5, d=5),
                            TuringDate(y=2006, m=10, d=2),
                            TuringDate(y=2006, m=10, d=3),
                            TuringDate(y=2006, m=10, d=4),
                            TuringDate(y=2006, m=10, d=5),
                            TuringDate(y=2006, m=10, d=6),
                            TuringDate(y=2007, m=1, d=1),
                            TuringDate(y=2007, m=1, d=2),
                            TuringDate(y=2007, m=1, d=3),
                            TuringDate(y=2007, m=2, d=19),
                            TuringDate(y=2007, m=2, d=20),
                            TuringDate(y=2007, m=2, d=21),
                            TuringDate(y=2007, m=2, d=22),
                            TuringDate(y=2007, m=2, d=23),
                            TuringDate(y=2007, m=5, d=1),
                            TuringDate(y=2007, m=5, d=2),
                            TuringDate(y=2007, m=5, d=3),
                            TuringDate(y=2007, m=5, d=4),
                            TuringDate(y=2007, m=5, d=7),
                            TuringDate(y=2007, m=10, d=1),
                            TuringDate(y=2007, m=10, d=2),
                            TuringDate(y=2007, m=10, d=3),
                            TuringDate(y=2007, m=10, d=4),
                            TuringDate(y=2007, m=10, d=5),
                            TuringDate(y=2007, m=12, d=31),
                            TuringDate(y=2008, m=1, d=1),
                            TuringDate(y=2008, m=2, d=6),
                            TuringDate(y=2008, m=2, d=7),
                            TuringDate(y=2008, m=2, d=8),
                            TuringDate(y=2008, m=2, d=11),
                            TuringDate(y=2008, m=2, d=12),
                            TuringDate(y=2008, m=4, d=4),
                            TuringDate(y=2008, m=5, d=1),
                            TuringDate(y=2008, m=5, d=2),
                            TuringDate(y=2008, m=6, d=9),
                            TuringDate(y=2008, m=9, d=15),
                            TuringDate(y=2008, m=9, d=29),
                            TuringDate(y=2008, m=9, d=30),
                            TuringDate(y=2008, m=10, d=1),
                            TuringDate(y=2008, m=10, d=2),
                            TuringDate(y=2008, m=10, d=3),
                            TuringDate(y=2009, m=1, d=1),
                            TuringDate(y=2009, m=1, d=2),
                            TuringDate(y=2009, m=1, d=26),
                            TuringDate(y=2009, m=1, d=27),
                            TuringDate(y=2009, m=1, d=28),
                            TuringDate(y=2009, m=1, d=29),
                            TuringDate(y=2009, m=1, d=30),
                            TuringDate(y=2009, m=4, d=6),
                            TuringDate(y=2009, m=5, d=1),
                            TuringDate(y=2009, m=5, d=28),
                            TuringDate(y=2009, m=5, d=29),
                            TuringDate(y=2009, m=10, d=1),
                            TuringDate(y=2009, m=10, d=2),
                            TuringDate(y=2009, m=10, d=5),
                            TuringDate(y=2009, m=10, d=6),
                            TuringDate(y=2009, m=10, d=7),
                            TuringDate(y=2009, m=10, d=8),
                            TuringDate(y=2010, m=1, d=1),
                            TuringDate(y=2010, m=2, d=15),
                            TuringDate(y=2010, m=2, d=16),
                            TuringDate(y=2010, m=2, d=17),
                            TuringDate(y=2010, m=2, d=18),
                            TuringDate(y=2010, m=2, d=19),
                            TuringDate(y=2010, m=4, d=5),
                            TuringDate(y=2010, m=5, d=3),
                            TuringDate(y=2010, m=6, d=14),
                            TuringDate(y=2010, m=6, d=15),
                            TuringDate(y=2010, m=6, d=16),
                            TuringDate(y=2010, m=9, d=22),
                            TuringDate(y=2010, m=9, d=23),
                            TuringDate(y=2010, m=9, d=24),
                            TuringDate(y=2010, m=10, d=1),
                            TuringDate(y=2010, m=10, d=4),
                            TuringDate(y=2010, m=10, d=5),
                            TuringDate(y=2010, m=10, d=6),
                            TuringDate(y=2010, m=10, d=7),
                            TuringDate(y=2011, m=1, d=3),
                            TuringDate(y=2011, m=2, d=2),
                            TuringDate(y=2011, m=2, d=3),
                            TuringDate(y=2011, m=2, d=4),
                            TuringDate(y=2011, m=2, d=7),
                            TuringDate(y=2011, m=2, d=8),
                            TuringDate(y=2011, m=4, d=4),
                            TuringDate(y=2011, m=4, d=5),
                            TuringDate(y=2011, m=5, d=2),
                            TuringDate(y=2011, m=6, d=6),
                            TuringDate(y=2011, m=9, d=12),
                            TuringDate(y=2011, m=10, d=3),
                            TuringDate(y=2011, m=10, d=4),
                            TuringDate(y=2011, m=10, d=5),
                            TuringDate(y=2011, m=10, d=6),
                            TuringDate(y=2011, m=10, d=7),
                            TuringDate(y=2012, m=1, d=2),
                            TuringDate(y=2012, m=1, d=3),
                            TuringDate(y=2012, m=1, d=23),
                            TuringDate(y=2012, m=1, d=24),
                            TuringDate(y=2012, m=1, d=25),
                            TuringDate(y=2012, m=1, d=26),
                            TuringDate(y=2012, m=1, d=27),
                            TuringDate(y=2012, m=4, d=2),
                            TuringDate(y=2012, m=4, d=3),
                            TuringDate(y=2012, m=4, d=4),
                            TuringDate(y=2012, m=4, d=30),
                            TuringDate(y=2012, m=5, d=1),
                            TuringDate(y=2012, m=6, d=22),
                            TuringDate(y=2012, m=10, d=1),
                            TuringDate(y=2012, m=10, d=2),
                            TuringDate(y=2012, m=10, d=3),
                            TuringDate(y=2012, m=10, d=4),
                            TuringDate(y=2012, m=10, d=5),
                            TuringDate(y=2013, m=1, d=1),
                            TuringDate(y=2013, m=1, d=2),
                            TuringDate(y=2013, m=1, d=3),
                            TuringDate(y=2013, m=2, d=11),
                            TuringDate(y=2013, m=2, d=12),
                            TuringDate(y=2013, m=2, d=13),
                            TuringDate(y=2013, m=2, d=14),
                            TuringDate(y=2013, m=2, d=15),
                            TuringDate(y=2013, m=4, d=4),
                            TuringDate(y=2013, m=4, d=5),
                            TuringDate(y=2013, m=4, d=29),
                            TuringDate(y=2013, m=4, d=30),
                            TuringDate(y=2013, m=5, d=1),
                            TuringDate(y=2013, m=6, d=10),
                            TuringDate(y=2013, m=6, d=11),
                            TuringDate(y=2013, m=6, d=12),
                            TuringDate(y=2013, m=9, d=19),
                            TuringDate(y=2013, m=9, d=20),
                            TuringDate(y=2013, m=10, d=1),
                            TuringDate(y=2013, m=10, d=2),
                            TuringDate(y=2013, m=10, d=3),
                            TuringDate(y=2013, m=10, d=4),
                            TuringDate(y=2013, m=10, d=7),
                            TuringDate(y=2014, m=1, d=1),
                            TuringDate(y=2014, m=1, d=31),
                            TuringDate(y=2014, m=2, d=3),
                            TuringDate(y=2014, m=2, d=4),
                            TuringDate(y=2014, m=2, d=5),
                            TuringDate(y=2014, m=2, d=6),
                            TuringDate(y=2014, m=4, d=7),
                            TuringDate(y=2014, m=5, d=1),
                            TuringDate(y=2014, m=5, d=2),
                            TuringDate(y=2014, m=6, d=2),
                            TuringDate(y=2014, m=9, d=8),
                            TuringDate(y=2014, m=10, d=1),
                            TuringDate(y=2014, m=10, d=2),
                            TuringDate(y=2014, m=10, d=3),
                            TuringDate(y=2014, m=10, d=6),
                            TuringDate(y=2014, m=10, d=7),
                            TuringDate(y=2015, m=1, d=1),
                            TuringDate(y=2015, m=1, d=2),
                            TuringDate(y=2015, m=2, d=18),
                            TuringDate(y=2015, m=2, d=19),
                            TuringDate(y=2015, m=2, d=20),
                            TuringDate(y=2015, m=2, d=23),
                            TuringDate(y=2015, m=2, d=24),
                            TuringDate(y=2015, m=4, d=6),
                            TuringDate(y=2015, m=5, d=1),
                            TuringDate(y=2015, m=6, d=22),
                            TuringDate(y=2015, m=9, d=3),
                            TuringDate(y=2015, m=9, d=4),
                            TuringDate(y=2015, m=10, d=1),
                            TuringDate(y=2015, m=10, d=2),
                            TuringDate(y=2015, m=10, d=5),
                            TuringDate(y=2015, m=10, d=6),
                            TuringDate(y=2015, m=10, d=7),
                            TuringDate(y=2016, m=1, d=1),
                            TuringDate(y=2016, m=2, d=8),
                            TuringDate(y=2016, m=2, d=9),
                            TuringDate(y=2016, m=2, d=10),
                            TuringDate(y=2016, m=2, d=11),
                            TuringDate(y=2016, m=2, d=12),
                            TuringDate(y=2016, m=4, d=4),
                            TuringDate(y=2016, m=5, d=2),
                            TuringDate(y=2016, m=6, d=9),
                            TuringDate(y=2016, m=6, d=10),
                            TuringDate(y=2016, m=9, d=15),
                            TuringDate(y=2016, m=9, d=16),
                            TuringDate(y=2016, m=10, d=3),
                            TuringDate(y=2016, m=10, d=4),
                            TuringDate(y=2016, m=10, d=5),
                            TuringDate(y=2016, m=10, d=6),
                            TuringDate(y=2016, m=10, d=7),
                            TuringDate(y=2017, m=1, d=2),
                            TuringDate(y=2017, m=1, d=27),
                            TuringDate(y=2017, m=1, d=30),
                            TuringDate(y=2017, m=1, d=31),
                            TuringDate(y=2017, m=2, d=1),
                            TuringDate(y=2017, m=2, d=2),
                            TuringDate(y=2017, m=4, d=3),
                            TuringDate(y=2017, m=4, d=4),
                            TuringDate(y=2017, m=5, d=1),
                            TuringDate(y=2017, m=5, d=29),
                            TuringDate(y=2017, m=5, d=30),
                            TuringDate(y=2017, m=10, d=2),
                            TuringDate(y=2017, m=10, d=3),
                            TuringDate(y=2017, m=10, d=4),
                            TuringDate(y=2017, m=10, d=5),
                            TuringDate(y=2017, m=10, d=6),
                            TuringDate(y=2018, m=1, d=1),
                            TuringDate(y=2018, m=2, d=15),
                            TuringDate(y=2018, m=2, d=16),
                            TuringDate(y=2018, m=2, d=19),
                            TuringDate(y=2018, m=2, d=20),
                            TuringDate(y=2018, m=2, d=21),
                            TuringDate(y=2018, m=4, d=5),
                            TuringDate(y=2018, m=4, d=6),
                            TuringDate(y=2018, m=4, d=30),
                            TuringDate(y=2018, m=5, d=1),
                            TuringDate(y=2018, m=6, d=18),
                            TuringDate(y=2018, m=9, d=24),
                            TuringDate(y=2018, m=10, d=1),
                            TuringDate(y=2018, m=10, d=2),
                            TuringDate(y=2018, m=10, d=3),
                            TuringDate(y=2018, m=10, d=4),
                            TuringDate(y=2018, m=10, d=5),
                            TuringDate(y=2018, m=12, d=31),
                            TuringDate(y=2019, m=1, d=1),
                            TuringDate(y=2019, m=2, d=4),
                            TuringDate(y=2019, m=2, d=5),
                            TuringDate(y=2019, m=2, d=6),
                            TuringDate(y=2019, m=2, d=7),
                            TuringDate(y=2019, m=2, d=8),
                            TuringDate(y=2019, m=4, d=5),
                            TuringDate(y=2019, m=5, d=1),
                            TuringDate(y=2019, m=5, d=2),
                            TuringDate(y=2019, m=5, d=3),
                            TuringDate(y=2019, m=6, d=7),
                            TuringDate(y=2019, m=9, d=13),
                            TuringDate(y=2019, m=10, d=1),
                            TuringDate(y=2019, m=10, d=2),
                            TuringDate(y=2019, m=10, d=3),
                            TuringDate(y=2019, m=10, d=4),
                            TuringDate(y=2019, m=10, d=7),
                            TuringDate(y=2020, m=1, d=1),
                            TuringDate(y=2020, m=1, d=24),
                            TuringDate(y=2020, m=1, d=27),
                            TuringDate(y=2020, m=1, d=28),
                            TuringDate(y=2020, m=1, d=29),
                            TuringDate(y=2020, m=1, d=30),
                            TuringDate(y=2020, m=4, d=6),
                            TuringDate(y=2020, m=5, d=1),
                            TuringDate(y=2020, m=5, d=4),
                            TuringDate(y=2020, m=5, d=5),
                            TuringDate(y=2020, m=6, d=25),
                            TuringDate(y=2020, m=6, d=26),
                            TuringDate(y=2020, m=10, d=1),
                            TuringDate(y=2020, m=10, d=2),
                            TuringDate(y=2020, m=10, d=5),
                            TuringDate(y=2020, m=10, d=6),
                            TuringDate(y=2020, m=10, d=7),
                            TuringDate(y=2020, m=10, d=8),
                            TuringDate(y=2021, m=1, d=1),
                            TuringDate(y=2021, m=2, d=11),
                            TuringDate(y=2021, m=2, d=12),
                            TuringDate(y=2021, m=2, d=15),
                            TuringDate(y=2021, m=2, d=16),
                            TuringDate(y=2021, m=2, d=17),
                            TuringDate(y=2021, m=4, d=5),
                            TuringDate(y=2021, m=5, d=3),
                            TuringDate(y=2021, m=5, d=4),
                            TuringDate(y=2021, m=5, d=5),
                            TuringDate(y=2021, m=6, d=14),
                            TuringDate(y=2021, m=9, d=20),
                            TuringDate(y=2021, m=9, d=21),
                            TuringDate(y=2021, m=10, d=1),
                            TuringDate(y=2021, m=10, d=4),
                            TuringDate(y=2021, m=10, d=5),
                            TuringDate(y=2021, m=10, d=6),
                            TuringDate(y=2021, m=10, d=7),
                            TuringDate(y=2022, m=1, d=3),
                            TuringDate(y=2022, m=2, d=1),
                            TuringDate(y=2022, m=2, d=2),
                            TuringDate(y=2022, m=2, d=3),
                            TuringDate(y=2022, m=2, d=4),
                            TuringDate(y=2022, m=4, d=5),
                            TuringDate(y=2022, m=6, d=3),
                            TuringDate(y=2022, m=10, d=3),
                            TuringDate(y=2022, m=10, d=4),
                            TuringDate(y=2022, m=10, d=5),
                            TuringDate(y=2023, m=1, d=2),
                            TuringDate(y=2023, m=1, d=23),
                            TuringDate(y=2023, m=1, d=24),
                            TuringDate(y=2023, m=1, d=25),
                            TuringDate(y=2023, m=1, d=26),
                            TuringDate(y=2023, m=1, d=27),
                            TuringDate(y=2023, m=4, d=5),
                            TuringDate(y=2023, m=5, d=1),
                            TuringDate(y=2023, m=6, d=22),
                            TuringDate(y=2023, m=9, d=29),
                            TuringDate(y=2023, m=10, d=2),
                            TuringDate(y=2023, m=10, d=3),
                            TuringDate(y=2023, m=10, d=4),
                            TuringDate(y=2023, m=10, d=5),
                            TuringDate(y=2024, m=1, d=1),
                            TuringDate(y=2024, m=2, d=12),
                            TuringDate(y=2024, m=2, d=13),
                            TuringDate(y=2024, m=2, d=14),
                            TuringDate(y=2024, m=2, d=15),
                            TuringDate(y=2024, m=4, d=4),
                            TuringDate(y=2024, m=5, d=1),
                            TuringDate(y=2024, m=6, d=10),
                            TuringDate(y=2024, m=9, d=17),
                            TuringDate(y=2024, m=10, d=1),
                            TuringDate(y=2024, m=10, d=2),
                            TuringDate(y=2024, m=10, d=3),
                            TuringDate(y=2024, m=10, d=4),
                            TuringDate(y=2025, m=1, d=1),
                            TuringDate(y=2025, m=1, d=29),
                            TuringDate(y=2025, m=1, d=30),
                            TuringDate(y=2025, m=1, d=31),
                            TuringDate(y=2025, m=2, d=3),
                            TuringDate(y=2025, m=4, d=4),
                            TuringDate(y=2025, m=5, d=1),
                            TuringDate(y=2025, m=10, d=1),
                            TuringDate(y=2025, m=10, d=2),
                            TuringDate(y=2025, m=10, d=3),
                            TuringDate(y=2025, m=10, d=4)]

precomputedChinaAdjustedWorkdays = [TuringDate(2005, 2, 5),
                                    TuringDate(2005, 2, 6),
                                    TuringDate(2005, 4, 30),
                                    TuringDate(2005, 5, 8),
                                    TuringDate(2005, 10, 8),
                                    TuringDate(2005, 10, 9),
                                    TuringDate(2005, 12, 31),
                                    TuringDate(2006, 1, 28),
                                    TuringDate(2006, 4, 29),
                                    TuringDate(2006, 4, 30),
                                    TuringDate(2006, 9, 30),
                                    TuringDate(2006, 12,30),
                                    TuringDate(2006, 12,31),
                                    TuringDate(2007, 2, 17),
                                    TuringDate(2007, 2, 25),
                                    TuringDate(2007, 4, 28),
                                    TuringDate(2007, 4, 29),
                                    TuringDate(2007, 9, 29),
                                    TuringDate(2007, 9, 30),
                                    TuringDate(2007, 12, 29),
                                    TuringDate(2008, 2, 2),
                                    TuringDate(2008, 2, 3),
                                    TuringDate(2008, 5, 4),
                                    TuringDate(2008, 9, 27),
                                    TuringDate(2008, 9, 28),
                                    TuringDate(2009, 1, 4),
                                    TuringDate(2009, 1, 24),
                                    TuringDate(2009, 2, 1),
                                    TuringDate(2009, 5, 31),
                                    TuringDate(2009, 9, 27),
                                    TuringDate(2009, 10, 10),
                                    TuringDate(2010, 2, 20),
                                    TuringDate(2010, 2, 21),
                                    TuringDate(2010, 6, 12),
                                    TuringDate(2010, 6, 13),
                                    TuringDate(2010, 9, 19),
                                    TuringDate(2010, 9, 25),
                                    TuringDate(2010, 9, 26),
                                    TuringDate(2010, 10, 9),
                                    TuringDate(2011, 1, 30),
                                    TuringDate(2011, 2, 12),
                                    TuringDate(2011, 4, 2),
                                    TuringDate(2011, 10, 8),
                                    TuringDate(2011, 10, 9),
                                    TuringDate(2011, 12, 31),
                                    TuringDate(2012, 1, 21),
                                    TuringDate(2012, 1, 29),
                                    TuringDate(2012, 3, 31),
                                    TuringDate(2012, 4, 1),
                                    TuringDate(2012, 4, 28),
                                    TuringDate(2012, 9, 29),
                                    TuringDate(2013, 1, 5),
                                    TuringDate(2013, 1, 6),
                                    TuringDate(2013, 2, 16),
                                    TuringDate(2013, 2, 17),
                                    TuringDate(2013, 4, 7),
                                    TuringDate(2013, 4, 27),
                                    TuringDate(2013, 4, 28),
                                    TuringDate(2013, 6, 8),
                                    TuringDate(2013, 6, 9),
                                    TuringDate(2013, 9, 22),
                                    TuringDate(2013, 9, 29),
                                    TuringDate(2013, 10, 12),
                                    TuringDate(2014, 1, 26),
                                    TuringDate(2014, 2, 8),
                                    TuringDate(2014, 5, 4),
                                    TuringDate(2014, 9, 28),
                                    TuringDate(2014, 10, 11),
                                    TuringDate(2015, 1, 4),
                                    TuringDate(2015, 2, 15),
                                    TuringDate(2015, 2, 28),
                                    TuringDate(2015, 9, 6),
                                    TuringDate(2015, 10, 10),
                                    TuringDate(2016, 2, 6),
                                    TuringDate(2016, 2, 14),
                                    TuringDate(2016, 6, 12),
                                    TuringDate(2016, 9, 18),
                                    TuringDate(2016, 10, 8),
                                    TuringDate(2016, 10, 9),
                                    TuringDate(2017, 1, 22),
                                    TuringDate(2017, 2, 4),
                                    TuringDate(2017, 4, 1),
                                    TuringDate(2017, 5, 27),
                                    TuringDate(2017, 9, 30),
                                    TuringDate(2018, 2, 11),
                                    TuringDate(2018, 2, 24),
                                    TuringDate(2018, 4, 8),
                                    TuringDate(2018, 4, 28),
                                    TuringDate(2018, 9, 29),
                                    TuringDate(2018, 9, 30),
                                    TuringDate(2018, 12, 29),
                                    TuringDate(2019, 2, 2),
                                    TuringDate(2019, 2, 3),
                                    TuringDate(2019, 4, 28),
                                    TuringDate(2019, 5, 5),
                                    TuringDate(2019, 9, 29),
                                    TuringDate(2019, 10, 12),
                                    TuringDate(2020, 1, 19),
                                    TuringDate(2020, 4, 26),
                                    TuringDate(2020, 5, 9),
                                    TuringDate(2020, 6, 28),
                                    TuringDate(2020, 9, 27),
                                    TuringDate(2020, 10, 10),
                                    TuringDate(2021, 2, 7),
                                    TuringDate(2021, 2, 20),
                                    TuringDate(2021, 4, 25),
                                    TuringDate(2021, 5, 8),
                                    TuringDate(2021, 9, 18),
                                    TuringDate(2021, 9, 26),
                                    TuringDate(2021, 10, 9)]


class TuringBusDayAdjustTypes(Enum):
    NONE = 1
    FOLLOWING = 2
    MODIFIED_FOLLOWING = 3
    PRECEDING = 4
    MODIFIED_PRECEDING = 5


class TuringCalendarTypes(Enum):
    NONE = 1
    WEEKEND = 2
    AUSTRALIA = 3
    CANADA = 4
    FRANCE = 5
    GERMANY = 6
    ITALY = 7
    JAPAN = 8
    NEW_ZEALAND = 9
    NORWAY = 10
    SWEDEN = 11
    SWITZERLAND = 12
    TARGET = 13
    UNITED_STATES = 14
    UNITED_KINGDOM = 15
    CHINA_SSE = 16
    CHINA_IB = 17


class TuringDateGenRuleTypes(Enum):
    FORWARD = 1
    BACKWARD = 2

###############################################################################


class TuringCalendar(object):
    ''' Class to manage designation of payment dates as holidays according to
    a regional or country-specific calendar convention specified by the user.
    It also supplies an adjustment method which takes in an adjustment
    convention and then applies that to any date that falls on a holiday in the
    specified calendar. '''

    def __init__(self,
                 calendarType: TuringCalendarTypes):
        ''' Create a calendar based on a specified calendar type. '''

        if calendarType not in TuringCalendarTypes:
            raise TuringError(
                "Need to pass FinCalendarType and not " +
                str(calendarType))

        self._type = calendarType

    ###########################################################################

    def adjust(self,
               dt: TuringDate,
               busDayConventionType: TuringBusDayAdjustTypes):
        ''' Adjust a payment date if it falls on a holiday according to the
        specified business day convention. '''

        if type(busDayConventionType) != TuringBusDayAdjustTypes:
            raise TuringError("Invalid type passed. Need FinBusDayConventionType")

        if busDayConventionType == TuringBusDayAdjustTypes.NONE:
            return dt

        elif busDayConventionType == TuringBusDayAdjustTypes.FOLLOWING:

            # step forward until we find a business day
            while self.isBusinessDay(dt) is False:
                dt = dt.addDays(1)

            return dt

        elif busDayConventionType == TuringBusDayAdjustTypes.MODIFIED_FOLLOWING:

            d_start = dt._d
            m_start = dt._m
            y_start = dt._y

            # step forward until we find a business day
            while self.isBusinessDay(dt) is False:
                dt = dt.addDays(1)

            # if the business day is in a different month look back
            # for previous first business day one day at a time
            # TODO: I could speed this up by starting it at initial date
            if dt._m != m_start:
                dt = TuringDate(y_start, m_start, d_start)
                while self.isBusinessDay(dt) is False:
                    dt = dt.addDays(-1)

            return dt

        elif busDayConventionType == TuringBusDayAdjustTypes.PRECEDING:

            # if the business day is in the next month look back
            # for previous first business day one day at a time
            while self.isBusinessDay(dt) is False:
                dt = dt.addDays(-1)

            return dt

        elif busDayConventionType == TuringBusDayAdjustTypes.MODIFIED_PRECEDING:

            d_start = dt._d
            m_start = dt._m
            y_start = dt._y

            # step backward until we find a business day
            while self.isBusinessDay(dt) is False:
                dt = dt.addDays(-1)

            # if the business day is in a different month look forward
            # for previous first business day one day at a time
            # I could speed this up by starting it at initial date
            if dt._m != m_start:
                dt = TuringDate(y_start, m_start, d_start)
                while self.isBusinessDay(dt) is False:
                    dt = dt.addDays(+1)

            return dt

        else:

            raise TuringError("Unknown adjustment convention" +
                              str(busDayConventionType))


###############################################################################

    def addBusinessDays(self,
                        startDate: TuringDate,
                        numDays: int):
        ''' Returns a new date that is numDays business days after TuringDate.
        All holidays in the chosen calendar are assumed not business days. '''

        # TODO: REMOVE DATETIME DEPENDENCE HERE ???

        if isinstance(numDays, int) is False:
            raise TuringError("Num days must be an integer")

        dt = datetime.date(startDate._y, startDate._m, startDate._d)
        d = dt.day
        m = dt.month
        y = dt.year
        newDt = TuringDate(y, m, d)

        s = +1
        if numDays < 0:
            numDays = -1 * numDays
            s = -1

        while numDays > 0:
            dt = dt + s * datetime.timedelta(days=1)
            d = dt.day
            m = dt.month
            y = dt.year
            newDt = TuringDate(y, m, d)

            if self.isBusinessDay(newDt) is True:
                numDays -= 1

        return newDt

###############################################################################

    def isBusinessDay(self,
                      dt: TuringDate):
        ''' Determines if a date is a business day according to the specified
        calendar. If it is it returns True, otherwise False. '''

        # For all calendars so far, SAT and SUN are not business days
        # If this ever changes I will need to add a filter here.
        if self._type == TuringCalendarTypes.CHINA_IB:
            if dt.isWeekend() and dt not in precomputedChinaAdjustedWorkdays:
                return False
        else:
            if dt.isWeekend():
                return False

        if self.isHoliday(dt) is True:
            return False
        else:
            return True

###############################################################################

    def isHoliday(self,
                  dt: TuringDate):
        ''' Determines if a date is a Holiday according to the specified
        calendar. Weekends are not holidays unless the holiday falls on a
        weekend date. '''

        startDate = TuringDate(dt._y, 1, 1)
        dayInYear = dt._excelDate - startDate._excelDate + 1
        weekday = dt._weekday

        self._y = dt._y
        self._m = dt._m
        self._d = dt._d
        self._dayInYear = dayInYear
        self._weekday = weekday
        self._dt = dt

        if self._type == TuringCalendarTypes.NONE:
            return self.HOLIDAY_NONE()
        elif self._type == TuringCalendarTypes.WEEKEND:
            return self.HOLIDAY_WEEKEND()
        elif self._type == TuringCalendarTypes.AUSTRALIA:
            return self.HOLIDAY_AUSTRALIA()
        elif self._type == TuringCalendarTypes.CANADA:
            return self.HOLIDAY_CANADA()
        elif self._type == TuringCalendarTypes.FRANCE:
            return self.HOLIDAY_FRANCE()
        elif self._type == TuringCalendarTypes.GERMANY:
            return self.HOLIDAY_GERMANY()
        elif self._type == TuringCalendarTypes.ITALY:
            return self.HOLIDAY_ITALY()
        elif self._type == TuringCalendarTypes.JAPAN:
            return self.HOLIDAY_JAPAN()
        elif self._type == TuringCalendarTypes.NEW_ZEALAND:
            return self.HOLIDAY_NEW_ZEALAND()
        elif self._type == TuringCalendarTypes.NORWAY:
            return self.HOLIDAY_NORWAY()
        elif self._type == TuringCalendarTypes.SWEDEN:
            return self.HOLIDAY_SWEDEN()
        elif self._type == TuringCalendarTypes.SWITZERLAND:
            return self.HOLIDAY_SWITZERLAND()
        elif self._type == TuringCalendarTypes.TARGET:
            return self.HOLIDAY_TARGET()
        elif self._type == TuringCalendarTypes.UNITED_KINGDOM:
            return self.HOLIDAY_UNITED_KINGDOM()
        elif self._type == TuringCalendarTypes.UNITED_STATES:
            return self.HOLIDAY_UNITED_STATES()
        elif self._type == TuringCalendarTypes.CHINA_SSE:
            return self.HOLIDAY_CHINA_SSE()
        elif self._type == TuringCalendarTypes.CHINA_IB:
            return self.HOLIDAY_CHINA_IB()
        else:
            print(self._type)
            raise TuringError("Unknown calendar")

###############################################################################

    def HOLIDAY_CHINA_SSE(self):
        """Holidays for SSE."""

        if self._dt in precomputedChinaHolidays:
            return True
        else:
            return False

###############################################################################

    def HOLIDAY_CHINA_IB(self):
        """Holidays for IB."""

        return self.HOLIDAY_CHINA_SSE()

###############################################################################

    def HOLIDAY_WEEKEND(self):
        ''' Weekends by themselves are a holiday. '''

        if self._dt.isWeekend():
            return True
        else:
            return False

###############################################################################

    def HOLIDAY_AUSTRALIA(self):
        ''' Only bank holidays. Weekends by themselves are not a holiday. '''

        m = self._m; d = self._d; y = self._y
        dayInYear = self._dayInYear
        weekday = self._weekday

        if m == 1 and d == 1:  # new years day
            return True

        if m == 1 and d == 26:  # Australia day
            return True

        if m == 1 and d == 27 and weekday == TuringDate.MON:  # Australia day
            return True

        if m == 1 and d == 28 and weekday == TuringDate.MON:  # Australia day
            return True

        em = easterMondayDay[y - 1901]

        if dayInYear == em - 3:  # good friday
            return True

        if dayInYear == em:  # Easter Monday
            return True

        if m == 4 and d == 25:  # Australia day
            return True

        if m == 4 and d == 26 and weekday == TuringDate.MON:  # Australia day
            return True

        if m == 6 and d > 7 and d < 15 and weekday == TuringDate.MON:  # Queen
            return True

        if m == 8 and d < 8 and weekday == TuringDate.MON:  # BANK holiday
            return True

        if m == 10 and d < 8 and weekday == TuringDate.MON:  # BANK holiday
            return True

        if m == 12 and d == 25:  # Xmas
            return True

        if m == 12 and d == 26 and weekday == TuringDate.MON:  # Xmas
            return True

        if m == 12 and d == 27 and weekday == TuringDate.MON:  # Xmas
            return True

        if m == 12 and d == 26:  # Boxing day
            return True

        if m == 12 and d == 27 and weekday == TuringDate.MON:  # Boxing
            return True

        if m == 12 and d == 28 and weekday == TuringDate.MON:  # Boxing
            return True

        return False

###############################################################################

    def HOLIDAY_UNITED_KINGDOM(self):
        ''' Only bank holidays. Weekends by themselves are not a holiday. '''

        m = self._m; d = self._d; y = self._y
        weekday = self._weekday ; dayInYear = self._dayInYear

        if m == 1 and d == 1:  # new years day
            return True

        if m == 1 and d == 2 and weekday == TuringDate.MON:  # new years day
            return True

        if m == 1 and d == 3 and weekday == TuringDate.MON:  # new years day
            return True

        em = easterMondayDay[y - 1901]

        if dayInYear == em:  # Easter Monday
            return True

        if dayInYear == em - 3:  # good friday
            return True

        if m == 5 and d <= 7 and weekday == TuringDate.MON:
            return True

        if m == 5 and d >= 25 and weekday == TuringDate.MON:
            return True

        if m == 6 and d == 2 and y == 2022: # SPRING BANK HOLIDAY
            return True

        if m == 6 and d == 3 and y == 2022: # QUEEN PLAT JUB
            return True

        if m == 8 and d > 24 and weekday == TuringDate.MON:  # Late Summer
            return True

        if m == 12 and d == 25:  # Xmas
            return True

        if m == 12 and d == 26:  # Boxing day
            return True

        if m == 12 and d == 27 and weekday == TuringDate.MON:  # Xmas
            return True

        if m == 12 and d == 27 and weekday == TuringDate.TUE:  # Xmas
            return True

        if m == 12 and d == 28 and weekday == TuringDate.MON:  # Xmas
            return True

        if m == 12 and d == 28 and weekday == TuringDate.TUE:  # Xmas
            return True

        return False

###############################################################################

    def HOLIDAY_FRANCE(self):
        ''' Only bank holidays. Weekends by themselves are not a holiday. '''

        m = self._m; d = self._d; y = self._y
        dayInYear = self._dayInYear

        if m == 1 and d == 1:  # new years day
            return True

        em = easterMondayDay[y - 1901]

        if dayInYear == em:  # Easter Monday
            return True

        if dayInYear == em - 3:  # good friday
            return True

        if m == 5 and d == 1: # LABOUR DAY
            return True

        if m == 5 and d == 8: # VICTORY DAY
            return True

        if dayInYear == em + 39 - 1:  # Ascension
            return True

        if dayInYear == em + 50 - 1:  # pentecost
            return True

        if m == 7 and d == 14: # BASTILLE DAY
            return True

        if m == 8 and d  == 15:  # ASSUMPTION
            return True

        if m == 11 and d == 1:  # ALL SAINTS
            return True

        if m == 11 and d == 11:  # ARMISTICE
            return True

        if m == 12 and d == 25:  # Xmas
            return True

        if m == 12 and d == 26:  # Boxing day
            return True

        return False

###############################################################################

    def HOLIDAY_SWEDEN(self):
        ''' Only bank holidays. Weekends by themselves are not a holiday. '''

        m = self._m; d = self._d; y = self._y
        dayInYear = self._dayInYear
        weekday = self._weekday

        if m == 1 and d == 1:  # new years day
            return True

        if m == 1 and d == 6:  # epiphany day
            return True

        em = easterMondayDay[y - 1901]

        if dayInYear == em - 3:  # good friday
            return True

        if dayInYear == em:  # Easter Monday
            return True

        if dayInYear == em + 39 - 1:  # Ascension
            return True

        if m == 5 and d == 1:  # labour day
            return True

        if m == 6 and d == 6: # June
            return True

        if m == 6 and d > 18 and d < 26 and weekday == TuringDate.FRI: # Midsummer
            return True

        if m == 12 and d == 24:  # Xmas eve
            return True

        if m == 12 and d == 25:  # Xmas
            return True

        if m == 12 and d == 26:  # Boxing day
            return True

        if m == 12 and d == 31:  # NYE
            return True

        return False

###############################################################################

    def HOLIDAY_GERMANY(self):
        ''' Only bank holidays. Weekends by themselves are not a holiday. '''

        m = self._m; d = self._d; y = self._y
        dayInYear = self._dayInYear

        if m == 1 and d == 1:  # new years day
            return True

        em = easterMondayDay[y - 1901]

        if dayInYear == em:  # Easter Monday
            return True

        if dayInYear == em - 3:  # good friday
            return True

        if m == 5 and d == 1: # LABOUR DAY
            return True

        if dayInYear == em + 39 - 1:  # Ascension
            return True

        if dayInYear == em + 50 - 1:  # pentecost
            return True

        if m == 10 and d == 3:  # GERMAN UNITY DAY
            return True

        if m == 12 and d == 24:  # Xmas eve
            return True

        if m == 12 and d == 25:  # Xmas
            return True

        if m == 12 and d == 26:  # Boxing day
            return True

        return False

###############################################################################

    def HOLIDAY_SWITZERLAND(self):
        ''' Only bank holidays. Weekends by themselves are not a holiday. '''

        m = self._m; d = self._d; y = self._y
        dayInYear = self._dayInYear

        if m == 1 and d == 1:  # new years day
            return True

        if m == 1 and d == 2:  # berchtoldstag
            return True

        em = easterMondayDay[y - 1901]

        if dayInYear == em:  # Easter Monday
            return True

        if dayInYear == em - 3:  # good friday
            return True

        if dayInYear == em + 39 - 1:  # Ascension
            return True

        if dayInYear == em + 50 - 1:  # pentecost / whit
            return True

        if m == 5 and d == 1:  # Labour day
            return True

        if m == 8 and d == 1:  # National day
            return True

        if m == 12 and d == 25:  # Xmas
            return True

        if m == 12 and d == 26:  # Boxing day
            return True

        return False

###############################################################################

    def HOLIDAY_JAPAN(self):
        ''' Only bank holidays. Weekends by themselves are not a holiday. '''

        m = self._m; d = self._d; y = self._y;
        weekday = self._weekday

        if m == 1 and d == 1:  # new years day
            return True

        if m == 1 and d == 2 and weekday == TuringDate.MON:  # bank holiday
            return True

        if m == 1 and d == 3 and weekday == TuringDate.MON:  # bank holiday
            return True

        if m == 1 and d > 7 and d < 15 and weekday == TuringDate.MON:  # coa
            return True

        if m == 2 and d == 11:  # nfd
            return True

        if m == 2 and d == 12 and weekday == TuringDate.MON:  # nfd
            return True

        if m == 2 and d == 23:  # emperor's birthday
            return True

        if m == 2 and d == 24 and weekday == TuringDate.MON:  # emperor's birthday
            return True

        if m == 3 and d == 20:  # vernal equinox - NOT EXACT
            return True

        if m == 3 and d == 21 and weekday == TuringDate.MON:
            return True

        if m == 4 and d == 29:  # SHOWA greenery
            return True

        if m == 4 and d == 30 and weekday == TuringDate.MON:  # SHOWA greenery
            return True

        if m == 5 and d == 3:  # Memorial Day
            return True

        if m == 5 and d == 4:  # nation
            return True

        if m == 5 and d == 5:  # children
            return True

        if m == 5 and d == 6 and weekday == TuringDate.MON:  # children
            return True

        if m == 7 and d > 14 and d < 22 and y != 2021 and weekday == TuringDate.MON:
            return True

        if m == 7 and d == 22 and y == 2021: # OLYMPICS
            return True

        if m == 7 and d == 23 and y == 2021: # OLYMPICS HEALTH AND SPORTS HERE
            return True

        # Mountain day
        if m == 8 and d == 11 and y != 2021:
            return True

        if m == 8 and d == 12 and y != 2021 and weekday == TuringDate.MON:
            return True

        if m == 8 and d == 9 and y == 2021 and weekday == TuringDate.MON:
            return True

        # Respect for aged
        if m == 9 and d > 14 and d < 22 and weekday == TuringDate.MON:
            return True

        # Equinox - APPROXIMATE
        if m == 9 and d == 23:
            return True

        if m == 9 and d == 24 and weekday == TuringDate.MON:
            return True

        if m == 10 and d > 7 and d <= 14 and y != 2021 and weekday == TuringDate.MON:  # HS
            return True

        if m == 11 and d == 3:  # Culture
            return True

        if m == 11 and d == 4 and weekday == TuringDate.MON:  # Culture
            return True

        if m == 11 and d == 23:  # Thanksgiving
            return True

        return False

###############################################################################

    def HOLIDAY_NEW_ZEALAND(self):
        ''' Only bank holidays. Weekends by themselves are not a holiday. '''

        m = self._m; d = self._d; y = self._y
        dayInYear = self._dayInYear
        weekday = self._weekday

        if m == 1 and d == 1:  # new years day
            return True

        if m == 1 and d == 2 and weekday == TuringDate.MON:  # new years day
            return True

        if m == 1 and d == 3 and weekday == TuringDate.MON:  # new years day
            return True

        if m == 1 and d > 18 and d < 26 and weekday == TuringDate.MON:  # Anniversary
            return True

        if m == 2 and d == 6:  # Waitanga day
            return True

        em = easterMondayDay[y - 1901]

        if dayInYear == em - 3:  # good friday
            return True

        if dayInYear == em:  # Easter Monday
            return True

        if m == 4 and d == 25:  # ANZAC day
            return True

        if m == 6 and d < 8 and weekday == TuringDate.MON:  # Queen
            return True

        if m == 10 and d > 21 and d < 29 and weekday == TuringDate.MON:  # LABOR DAY
            return True

        if m == 12 and d == 25:  # Xmas
            return True

        if m == 12 and d == 26 and weekday == TuringDate.MON:  # Xmas
            return True

        if m == 12 and d == 27 and weekday == TuringDate.MON:  # Xmas
            return True

        if m == 12 and d == 26:  # Boxing day
            return True

        if m == 12 and d == 27 and weekday == TuringDate.MON:  # Boxing
            return True

        if m == 12 and d == 28 and weekday == TuringDate.MON:  # Boxing
            return True

        return False

###############################################################################

    def HOLIDAY_NORWAY(self):
        ''' Only bank holidays. Weekends by themselves are not a holiday. '''

        m = self._m; d = self._d; y = self._y
        dayInYear = self._dayInYear

        if m == 1 and d == 1:  # new years day
            return True

        em = easterMondayDay[y - 1901]

        if dayInYear == em - 4:  # holy thursday
            return True

        if dayInYear == em - 3:  # good friday
            return True

        if dayInYear == em:  # Easter Monday
            return True

        if dayInYear == em + 38:  # Ascension
            return True

        if dayInYear == em + 49:  # Pentecost
            return True

        if m == 5 and d == 1:  # May day
            return True

        if m == 5 and d == 17:  # Independence day
            return True

        if m == 12 and d == 25:  # Xmas
            return True

        if m == 12 and d == 26:  # Boxing day
            return True

        return False

###############################################################################

    def HOLIDAY_UNITED_STATES(self):
        ''' Only bank holidays. Weekends by themselves are not a holiday.
        This is a generic US calendar that contains the superset of
        holidays for bond markets, NYSE, and public holidays. For each of
        these and other categories there will be some variations. '''

        m = self._m; d = self._d;
        weekday = self._weekday

        if m == 1 and d == 1:  # NYD
            return True

        if m == 1 and d == 2 and weekday == TuringDate.MON:  # NYD
            return True

        if m == 1 and d == 3 and weekday == TuringDate.MON:  # NYD
            return True

        if m == 1 and d >= 15 and d < 22 and weekday == TuringDate.MON:  # MLK
            return True

        if m == 2 and d >= 15 and d < 22 and weekday == TuringDate.MON:  # GW
            return True

        if m == 5 and d >= 25 and d <= 31 and weekday == TuringDate.MON:  # MD
            return True

        if m == 7 and d == 4:  # Indep day
            return True

        if m == 7 and d == 5 and weekday == TuringDate.MON:  # Indep day
            return True

        if m == 7 and d == 3 and weekday == TuringDate.FRI:  # Indep day
            return True

        if m == 9 and d >= 1 and d < 8 and weekday == TuringDate.MON:  # Lab
            return True

        if m == 10 and d >= 8 and d < 15 and weekday == TuringDate.MON:  # CD
            return True

        if m == 11 and d == 11:  # Veterans day
            return True

        if m == 11 and d == 12 and weekday == TuringDate.MON:  # Vets
            return True

        if m == 11 and d == 10 and weekday == TuringDate.FRI:  # Vets
            return True

        if m == 11 and d >= 22 and d < 29 and weekday == TuringDate.THU:  # TG
            return True

        if m == 12 and d == 24 and weekday == TuringDate.FRI:  # Xmas holiday
            return True

        if m == 12 and d == 25:  # Xmas holiday
            return True

        if m == 12 and d == 26 and weekday == TuringDate.MON:  # Xmas holiday
            return True

        if m == 12 and d == 31 and weekday == TuringDate.FRI:
            return True

        return False

###############################################################################

    def HOLIDAY_CANADA(self):
        ''' Only bank holidays. Weekends by themselves are not a holiday. '''

        m = self._m; d = self._d; y = self._y
        weekday = self._weekday; dayInYear = self._dayInYear

        if m == 1 and d == 1:  # NYD
            return True

        if m == 1 and d == 2 and weekday == TuringDate.MON:  # NYD
            return True

        if m == 1 and d == 3 and weekday == TuringDate.MON:  # NYD
            return True

        if m == 2 and d >= 15 and d < 22 and weekday == TuringDate.MON:  # FAMILY
            return True

        em = easterMondayDay[y - 1901]

        if dayInYear == em - 3:  # good friday
            return True

        if m == 5 and d >= 18 and d < 25 and weekday == TuringDate.MON:  # VICTORIA
            return True

        if m == 7 and d == 1:  # Canada day
            return True

        if m == 7 and d == 2 and weekday == TuringDate.MON:  # Canada day
            return True

        if m == 7 and d == 3 and weekday == TuringDate.MON:  # Canada day
            return True

        if m == 8 and d < 8 and weekday == TuringDate.MON:  # Provincial
            return True

        if m == 9 and d < 8 and weekday == TuringDate.MON:  # Labor
            return True

        if m == 10 and d >= 8 and d < 15 and weekday == TuringDate.MON:  # THANKS
            return True

        if m == 11 and d == 11:  # Veterans day
            return True

        if m == 11 and d == 12 and weekday == TuringDate.MON:  # Vets
            return True

        if m == 11 and d == 13 and weekday == TuringDate.MON:  # Vets
            return True

        if m == 12 and d == 25:  # Xmas holiday
            return True

        if m == 12 and d == 26 and weekday == TuringDate.MON:  # Xmas holiday
            return True

        if m == 12 and d == 27 and weekday == TuringDate.MON:  # Xmas holiday
            return True

        if m == 12 and d == 26:  # Boxing holiday
            return True

        if m == 12 and d == 27 and weekday == TuringDate.MON:  # Boxing holiday
            return True

        if m == 12 and d == 28 and weekday == TuringDate.TUE:  # Boxing holiday
            return True

        return False

###############################################################################

    def HOLIDAY_ITALY(self):
        ''' Only bank holidays. Weekends by themselves are not a holiday. '''

        m = self._m
        d = self._d
        y = self._y
        dayInYear = self._dayInYear

        if m == 1 and d == 1:  # new years day
            return True

        if m == 1 and d == 6:  # epiphany
            return True

        em = easterMondayDay[y - 1901]

        if dayInYear == em:  # Easter Monday
            return True

        if dayInYear == em - 3:  # good friday
            return True

        if m == 4 and d == 25:  # LIBERATION DAY
            return True

        if m == 5 and d == 1:  # LABOUR DAY
            return True

        if m == 6 and d == 2 and y > 1999:  # REPUBLIC DAY
            return True

        if m == 8 and d == 15:  # ASSUMPTION
            return True

        if m == 11 and d == 1:  # ALL SAINTS
            return True

        if m == 12 and d == 8:  # IMMAC CONC
            return True

        if m == 12 and d == 25:  # Xmas
            return True

        if m == 12 and d == 26:  # Boxing day
            return True

        return False

###############################################################################

    def HOLIDAY_TARGET(self):
        ''' Only bank holidays. Weekends by themselves are not a holiday. '''

        m = self._m
        d = self._d
        y = self._y
        dayInYear = self._dayInYear

        if m == 1 and d == 1:  # new year's day
            return True

        if m == 5 and d == 1:  # May day
            return True

        em = easterMondayDay[y - 1901]

        if dayInYear == em - 3:  # Easter Friday holiday
            return True

        if dayInYear == em:  # Easter monday holiday
            return True

        if m == 12 and d == 25:  # Xmas bank holiday
            return True

        if m == 12 and d == 26:  # Xmas bank holiday
            return True

        return False

###############################################################################

    def HOLIDAY_NONE(self):
        ''' No day is a holiday. '''
        return False

###############################################################################

    def getHolidayList(self,
                       year: float):
        ''' generates a list of holidays in a specific year for the specified
        calendar. Useful for diagnostics. '''
        startDate = TuringDate(year, 1, 1)
        endDate = TuringDate(year + 1, 1, 1)
        holidayList = []
        while startDate < endDate:
            if self.isBusinessDay(startDate) is False and \
              startDate.isWeekend() is False:
                holidayList.append(startDate.__str__())

            startDate = startDate.addDays(1)

        return holidayList

###############################################################################

    def easterMonday(self,
                     year: float):
        ''' Get the day in a given year that is Easter Monday. This is not
        easy to compute so we rely on a pre-calculated array. '''

        if year > 2100:
            raise TuringError(
                "Unable to determine Easter monday in year " + str(year))

        emDays = easterMondayDay[year - 1901]
        startDate = TuringDate(year, 1, 1)
        em = startDate.addDays(emDays-1)
        return em

###############################################################################

    def __str__(self):
        s = self._type.name
        return s

###############################################################################

    def __repr__(self):
        s = self._type
        return s

###############################################################################
