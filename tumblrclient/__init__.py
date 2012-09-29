#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2012 Martin Spier ( spiermar@gmail.com ) All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


'''Python Tumblr client.'''

__author__ = 'spiermar@gmail.com'
__version__ = '0.1'

import oauth2 as oauth
import urllib
import urlparse
import json
import logging
import ConfigParser
import os
import sys
from time import gmtime, strftime

class TumblrClient:
	
	def __init__(self):
		#opening logger
		self.logger = logging.getLogger('tumblrclient')
		
		#Load configuration file
		self.load_config()
		
		#Creating the OAuth consumer and client
		consumer = oauth.Consumer(self.consumer_key, self.consumer_secret)
		self.client = oauth.Client(consumer)
		self.client.add_credentials(self.account,self.password)
		
		#Building request body
		params = {}
		params["x_auth_username"] = self.account
		params["x_auth_password"] = self.password
		params["x_auth_mode"] = 'client_auth'

		#Setting signature method
		self.client.set_signature_method = oauth.SignatureMethod_HMAC_SHA1()
		
		#Requesting the OAuth request token
		content = self.make_oauth_request(self.access_token_url,'POST',urllib.urlencode(params))
		
		if content is None:
			self.logger.critical("Error requesting OAuth token")
			raise Exception("Error requesting OAuth token")
		
		self.logger.info("Authentication successful")
		
		request_token = dict(urlparse.parse_qsl(content))

		self.logger.debug("oauth_token: %s" % request_token['oauth_token'])
		self.logger.debug("oauth_token_secret: %s" % request_token['oauth_token_secret'])

		#Converting request token to access token
		access_token = oauth.Token(request_token["oauth_token"], request_token["oauth_token_secret"])

		#Creating an OAuth client with the new access token
		self.client = oauth.Client(consumer, access_token)
		
	def make_oauth_request(self,request_url,method='GET',body=None):
		self.logger.debug("request url: %s" % str(request_url))
		self.logger.debug("request method: %s " % str(method))
		self.logger.debug("request body: %s " % str(body))
		if method.upper() == 'POST':
			resp, content = self.client.request(request_url,'POST',body)
		elif method.upper() == 'GET':
			resp, content = self.client.request(request_url,'GET')
		else:
			self.logger.error("Invalid method: %s" % method)
			return None
		self.logger.debug("resp: %s " % str(resp))
		self.logger.debug("content: %s " % str(content))
		if resp['status'] not in ('200','201'):
			self.logger.error("Invalid response: %s" % resp['status'])
			return None
		
		return content
			
	def make_unauthorized_request(self,request_url):
		content = urllib.urlopen(request_url)

		return content
		
	def parse_json(self,content_json):
		try:
			content_dict = json.loads(content_json)
		except ValueError, e:
			self.logger.error('Invalid response: %s (%d)' % (e,e.getcode()))
			return None

		return content_dict
	
	def load_config(self):
		#constants
		CONFIG_FILE = 'tumblrclient.config'
		
		self.logger.debug("Loading configuration file: %s" % os.path.dirname(os.path.abspath(__file__)) + '/' + CONFIG_FILE)
		
		#Check if the configuration file exists
		if os.path.isfile(os.path.dirname(os.path.abspath(__file__)) + '/' + CONFIG_FILE) == False:
			self.logger.error("Configuration file was not found.")
			raise Exception("Configuration file was not found.")

		try:
			#Loading configuration file
			config = ConfigParser.SafeConfigParser()
			config.read(os.path.dirname(os.path.abspath(__file__)) + '/' + CONFIG_FILE)

			#Loading necessary parameters
			self.consumer_key = config.get('tumblrclient', 'consumer_key')
			self.consumer_secret = config.get('tumblrclient', 'consumer_secret')
			self.account = config.get('tumblrclient', 'account')
			self.password = config.get('tumblrclient', 'password')
			self.access_token_url = config.get('tumblrclient', 'access_token_url')
			self.limit = config.get('tumblrclient', 'limit')
			self.blog = config.get('tumblrclient', 'blog')
			self.logger.info("The configuration filed was loaded successfully")
		except ConfigParser.NoSectionError, e:
			self.logger.critical("The configuration file was not found or the file structure is invalid: %s." % e)
			raise Exception("The configuration file was not found or the file structure is invalid: ", e)
		except ConfigParser.ParsingError, e:
			self.logger.critical("The configuration file was not found or the file structure is invalid: %s." % e)
			raise Exception("The configuration file was not found or the file structure is invalid: ", e)
		except ConfigParser.NoOptionError, e:
			self.logger.critical("The configuration file was not found or the file structure is invalid. %s:" % e)
			raise Exception("The configuration file was not found or the file structure is invalid: ", e)
		except:
			self.logger.critical("Unexpected error: %s." % sys.exc_info()[0])
			raise Exception("Unexpected error: " % sys.exc_info()[0])
		
	def unlike(self,post_id, reblog_key):
		#Building request body
		params = {}
		params["id"] = post_id
		params["reblog_key"] = reblog_key
		
		self.logger.info("Unliking post: %s" % post_id)
		
		#Sending unlike API request
		content = self.make_oauth_request('http://api.tumblr.com/v2/user/unlike','POST',urllib.urlencode(params))
		
		if content is None:
			self.logger.error("Error unliking post: %s" % post_id)
			return False
		
		self.logger.info("Post unliked successfully: %s" % post_id)

		return True

	def likes(self,offset=0):
		#Building request body
		params = {}
		params["offset"] = offset
		params["limit"] = self.limit
		
		self.logger.info("Downloading user likes")
		
		#Sending unlike API request
		content_json = self.make_oauth_request('http://api.tumblr.com/v2/user/likes','POST',urllib.urlencode(params))
		
		if content_json is None:
			self.logger.error("Error downloading user likes")
			return None
		
		content = self.parse_json(content_json)
		
		if content is None:
			self.logger.error("Error downloading user likes")
			return None
		
		self.logger.info("Liked posts: %s" % content['response']['liked_count'])
		
		posts = content['response']['liked_posts']
		
		self.logger.info("Posts fetched: %s" % len(posts))

		return posts
	
	def reblog(self,post_id,reblog_key,state,comment):
		#Building request body
		params = {}
		params["id"] = post_id
		params["reblog_key"] = reblog_key
		params["state"] = state
		params["comment"] = comment
		
		self.logger.info("Submitting post: %s" % post_id)
		
		#Sending unlike API request
		content_json = self.make_oauth_request("http://api.tumblr.com/v2/blog/%s/post/reblog" % self.blog,'POST',urllib.urlencode(params))
		
		if content_json is None:
			self.logger.error("Error submitting post: %s" % post_id)
			return None
		
		content = self.parse_json(content_json)
		
		if content is None:
			self.logger.error("Error submitting post: %s" % post_id)
			return None
		
		reblog_id =  content['response']['id']
		
		self.logger.info("Post \"%s\" submitted under \"%s\" reblog id" % (post_id,reblog_id))
		
		return reblog_id
	
	def edit(self,post_id,params):
		params['id'] = post_id
		
		self.logger.info("Edit post \"%s\" with parameters \"%s\"" % (post_id,str(params)))
		
		#Sending edit API request
		content_json = self.make_oauth_request("http://api.tumblr.com/v2/blog/%s/post/edit" % self.blog,'POST',urllib.urlencode(params))
		
		if content_json is None:
			self.logger.error("Error editing post: %s" % post_id)
			return False
		
		content = self.parse_json(content_json)
		
		if content is None:
			self.logger.error("Error editing post: %s" % post_id)
			return False
		
		self.logger.info("Post edited: %s" % post_id)
		
		return True
	
	def followers(self):
		self.logger.info("Retrieving blog followers for blog %s" % self.blog)
		
		#Sending followers API request
		content_json = self.make_oauth_request("http://api.tumblr.com/v2/blog/%s/followers" % self.blog)
		
		if content_json is None:
			self.logger.error("Error retrieving blog followers for blog %s" % self.blog)
			return None
		
		content = self.parse_json(content_json)
		
		if content is None:
			self.logger.error("Error retrieving blog followers for blog %s" % self.blog)
			return None
		
		self.logger.info("Blog followers were retrieved successfully")
		
		return content
	
	def follow(self,url):
		params['url'] = url
		
		self.logger.info("Requesting follow blog \"%s\"" % (post_id,str(params)))
		
		#Sending edit API request
		content_json = self.make_oauth_request("api.tumblr.com/v2/user/follow",'POST',urllib.urlencode(params))
		
		if content_json is None:
			self.logger.error("Error following blog \"%s\"" % url)
			return False
		
		content = self.parse_json(content_json)
		
		if content is None:
			self.logger.error("Error following blog \"%s\"" % url)
			return False
		
		self.logger.info("Following blog \"%s\"" % url)
		
		return True
		
				