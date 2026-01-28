Feature: Health Check API

	@health_check
	Scenario Outline: Verify Health Check API Response
		Given url "healthCheck"
		When method "GET"
		Then status "<status_code>"
		And match response == "<responseBody>"

		@wip
		Examples:
			| status_code | responseBody               |
			| 200         | healthCheck.validHealthCheckResponse |
			# | 503         | "Service is unavailable"   |