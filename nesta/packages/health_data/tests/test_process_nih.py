import mock
import pandas as pd
import pytest

from nesta.packages.health_data.process_nih import _extract_date
from nesta.packages.health_data.process_nih import _geocode
from nesta.packages.health_data.process_nih import geocode_dataframe


class TestExtractDateSuccess():
    def test_string_date_pattern(self):
        assert _extract_date('Sep 21 2017') == '2017-09-21'
        assert _extract_date('Mar  1 2011') == '2011-03-01'
        assert _extract_date('Apr  7 2009') == '2009-04-07'
        assert _extract_date('January 2016') == '2016-01-01'
        assert _extract_date('Oct 2014') == '2014-10-01'
        assert _extract_date('2015') == '2015-01-01'
        assert _extract_date('6 April 2018') == '2018-04-06'
        assert _extract_date('8 Dec, 2010') == '2010-12-08'

    def test_dash_date_pattern(self):
        assert _extract_date('2016-07-31') == '2016-07-31'
        assert _extract_date('2010-12-01') == '2010-12-01'
        assert _extract_date('2020-01-04') == '2020-01-04'

    def test_slash_date_pattern(self):
        assert _extract_date('5/31/2020') == '2020-05-31'
        assert _extract_date('11/1/2012') == '2012-11-01'
        assert _extract_date('1/1/2010') == '2010-01-01'
        assert _extract_date('2000/12/01') == '2000-12-01'
        assert _extract_date('1999/04/20') == '1999-04-20'

    def test_invalid_month_returns_year(self):
        assert _extract_date('Cat 12 2009') == '2009-01-01'
        assert _extract_date('2000-19-09') == '2000-01-01'
        assert _extract_date('20/4/2009') == '2009-01-01'

    def test_invalid_day_returns_year(self):
        assert _extract_date('Mar 38 2001') == '2001-01-01'
        assert _extract_date('2000-09-40') == '2000-01-01'
        assert _extract_date('5/32/2017') == '2017-01-01'

    def test_valid_year_extract(self):
        assert _extract_date('2019') == '2019-01-01'
        assert _extract_date('sometime in 2011') == '2011-01-01'
        assert _extract_date('maybe 2019 or 2020') == '2019-01-01'

    def test_invalid_year_returns_none(self):
        assert _extract_date('no year') is None
        assert _extract_date('nan') is None
        assert _extract_date('-') is None


class TestGeocoding():
    @staticmethod
    @pytest.fixture
    def mocked_osm_response():
        mocked_response = mock.Mock()
        mocked_response.json.return_value = [{'lat': '12.923432', 'lon': '-75.234569'}]
        return mocked_response

    def test_error_raised_when_arguments_missing(self):
        with pytest.raises(TypeError) as e:
            _geocode()
        assert "Missing argument" in str(e.value)

    @mock.patch('nesta.packages.geo_utils.geocode.requests.get')
    def test_coordindates_of_first_result_extracted_from_json_with_multiple_results(self, mocked_request):
        mocked_response = mock.Mock()
        mocked_response.json.return_value = [
                    {'lat': '123', 'lon': '456'},
                    {'lat': '111', 'lon': '222'},
                    {'lat': '777', 'lon': '888'}
                    ]
        mocked_request.return_value = mocked_response
        assert _geocode('best match') == mocked_response.json.return_value[0]


class TestGeocodeDataFrame():
    @staticmethod
    @pytest.fixture
    def test_dataframe():
        df = pd.DataFrame({'index': [0, 1, 2],
                           'city': ['London', 'Sheffield', 'Brussels'],
                           'country': ['UK', 'United Kingdom', 'Belgium'],
                       })
        return df

    @mock.patch('nesta.packages.health_data.process_nih._geocode')
    def test_underlying_geocoding_function_called_with_city_country(self, mocked_geocode,
                                                                    test_dataframe):
        # Generate dataframe using a mocked output
        mocked_geocode.side_effect = ['cat', 'dog', 'squirrel']
        geocoded_dataframe = geocode_dataframe(test_dataframe)

        # Expected outputs
        expected_dataframe = pd.DataFrame({'index': [0, 1, 2],
                                           'city': ['London', 'Sheffield', 'Brussels'],
                                           'country': ['UK', 'United Kingdom', 'Belgium'],
                                           'coordinates': ['cat', 'dog', 'squirrel']
                                       })
        expected_calls = [mock.call(city='London', country='UK'),
                          mock.call(city='Sheffield', country='United Kingdom'),
                          mock.call(city='Brussels', country='Belgium')]

        # Check expected behaviours
        assert geocoded_dataframe.equals(expected_dataframe)
        mocked_geocode.assert_has_calls(expected_calls)

    @mock.patch('nesta.packages.health_data.process_nih._geocode')
    def test_underlying_geocoding_function_called_with_query_fallback(self, mocked_geocode, 
                                                                      test_dataframe):
        mocked_geocode.side_effect = [None, None, None, 'dog', 'cat', 'squirrel']
        geocoded_dataframe = geocode_dataframe(test_dataframe)
        # Expected outputs
        expected_dataframe = pd.DataFrame({'index': [0, 1, 2],
                                           'city': ['London', 'Sheffield', 'Brussels'],
                                           'country': ['UK', 'United Kingdom', 'Belgium'],
                                           'coordinates': ['dog', 'cat', 'squirrel']
                                       })
        expected_calls = [mock.call(city='London', country='UK'),
                          mock.call(city='Sheffield', country='United Kingdom'),
                          mock.call(city='Brussels', country='Belgium'),
                          mock.call('London UK'),
                          mock.call('Sheffield United Kingdom'),
                          mock.call('Brussels Belgium')]
        # Check expected behaviours
        assert geocoded_dataframe.equals(expected_dataframe)
        mocked_geocode.assert_has_calls(expected_calls)

    ##  Removing because implicit in decorator
    # @mock.patch('nesta.packages.health_data.process_nih._geocode')
    # def test_time_between_calls_not_less_than_1_second(self, mocked_geocode, test_dataframe):

    #     start_time = time.time()
    #     _side_effect = iter(['cat', 'dog', 'squirrel'])
    #     times = []
    #     def side_effect(*args, **kwargs):            
    #         times.append(time.time() - start_time)
    #         return next(_side_effect)

    #     mocked_geocode.side_effect = side_effect
    #     geocoded_dataframe = geocode_dataframe(test_dataframe)

    #     last_time = -1
    #     for i, _time in enumerate(times):
    #         assert _time > last_time + 1
    #         last_time = _time


    @mock.patch('nesta.packages.health_data.process_nih._geocode')
    def test_duplicates_are_only_geocoded_once(self, mocked_geocode):
        test_dataframe = pd.DataFrame({'index': [0, 1, 2, 3],
                                       'city': ['London', 'Brussels', 'London', 'Brussels'],
                                       'country': ['UK', 'Belgium', 'UK', 'Belgium']
                                   })

        mocked_geocode.side_effect = ['LON', 'BRU']
        geocoded_dataframe = geocode_dataframe(test_dataframe)

        expected_dataframe = pd.DataFrame({'index': [0, 1, 2, 3],
                                           'city': ['London', 'Brussels', 'London', 'Brussels'],
                                           'country': ['UK', 'Belgium', 'UK', 'Belgium'],
                                           'coordinates': ['LON', 'BRU', 'LON', 'BRU']
                                       })
        assert geocoded_dataframe.equals(expected_dataframe)
        assert mocked_geocode.call_count == 2