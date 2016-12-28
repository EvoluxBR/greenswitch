#!/usr/bin/env python
# -*- coding: utf-8 -*-

from textwrap import dedent
import types

import gevent

from greenswitch import esl
from tests import TestInboundESLBase
from tests import fakeeslserver


class TestInboundESL(TestInboundESLBase):
    def test_connect(self):
        """Should connect in FreeSWITCH ESL Server."""
        switch_esl = fakeeslserver.FakeESLServer('0.0.0.0', 8022, 'ClueCon')
        switch_esl.start_server()
        esl_ = esl.InboundESL('127.0.0.1', 8022, 'ClueCon')
        esl_.connect()
        self.assertTrue(esl_.connected)
        self.assertTrue(esl_._auth_request_event.is_set())
        self.assertEqual(esl_.sock.gettimeout(), None)
        esl_.stop()
        switch_esl.stop()

    def test_connect_wrong_password(self):
        """Should raises ValueError when using wrong ESL password."""
        switch_esl = fakeeslserver.FakeESLServer('0.0.0.0', 8022, 'ClueCon')
        switch_esl.start_server()
        esl_ = esl.InboundESL('127.0.0.1', 8022, 'wrongpassword')
        self.assertRaises(ValueError, esl_.connect)
        switch_esl.stop()
        self.assertFalse(esl_.connected)
        esl_.stop()

    def test_client_disconnect(self):
        """Should disconnect properly."""
        self.esl.stop()
        gevent.sleep(0.01)
        self.assertFalse(self.esl.connected)
        self.switch_esl.stop()

    def test_z_server_disconnect(self):
        """Should detect server disconnection."""
        self.switch_esl.stop()
        gevent.sleep(0.01)
        self.assertFalse(self.esl.connected)

    def test_register_unregister_handle(self):
        """Should register/unregister handler for events."""
        def handle(event):
            pass
        self.esl.register_handle('TEST_EVENT', handle)
        self.assertIn(handle, self.esl.event_handlers['TEST_EVENT'])
        self.esl.unregister_handle('TEST_EVENT', handle)
        self.assertNotIn('TEST_EVENT', self.esl.event_handlers)

    def test_register_a_registered_handle(self):
        """Should not register the same handler to same event."""
        def handle(event):
            pass
        self.esl.register_handle('TEST_EVENT', handle)
        self.esl.register_handle('TEST_EVENT', handle)
        self.assertEqual([handle], self.esl.event_handlers['TEST_EVENT'])

    def test_unregister_a_not_registered_handle(self):
        """Should raise ValueError when unregistering an unknown handler."""
        def handle(event):
            pass
        with self.assertRaises(ValueError):
            self.esl.unregister_handle('TEST_EVENT', handle)

    def test_custom_event(self):
        """Should call registered handler for CUSTOM events."""
        def on_sofia_pre_register(self, event):
            self.pre_register = True

        self.esl.pre_register = False
        self.esl.on_sofia_pre_register = types.MethodType(
            on_sofia_pre_register, self.esl)

        self.esl.register_handle('sofia::pre_register',
                                 self.esl.on_sofia_pre_register)
        event_plain = dedent("""\
            Event-Name: CUSTOM
            Event-Subclass: sofia::pre_register""")
        self.send_fake_event_plain(event_plain)
        self.assertTrue(self.esl.pre_register)

    def test_event(self):
        """Should call registered handler for events."""
        def on_heartbeat(self, event):
            self.heartbeat = True

        self.esl.heartbeat = False
        self.esl.on_heartbeat = types.MethodType(
            on_heartbeat, self.esl)

        self.esl.register_handle('HEARTBEAT', self.esl.on_heartbeat)
        event_plain = dedent("""\
            Event-Name: HEARTBEAT
            Core-UUID: cb2d5146-9a99-11e4-9291-092b1a87b375
            FreeSWITCH-Hostname: evoluxdev
            FreeSWITCH-Switchname: freeswitch
            FreeSWITCH-IPv4: 172.16.7.47
            FreeSWITCH-IPv6: %3A%3A1
            Event-Date-Local: 2015-01-19%2012%3A06%3A19
            Event-Date-GMT: Mon,%2019%20Jan%202015%2015%3A06%3A19%20GMT
            Event-Date-Timestamp: 1421679979428652
            Event-Calling-File: switch_core.c
            Event-Calling-Function: send_heartbeat
            Event-Calling-Line-Number: 70
            Event-Sequence: 23910
            Event-Info: System%20Ready
            Up-Time: 0%20years,%201%20day,%2016%20hours,%2053%20minutes,%2014%20seconds,%20552%20milliseconds,%2035%20microseconds
            FreeSWITCH-Version: 1.5.15b%2Bgit~20141226T052811Z~0a66db6f12~64bit
            Uptime-msec: 147194552
            Session-Count: 0
            Max-Sessions: 1000
            Session-Per-Sec: 30
            Session-Per-Sec-Max: 2
            Session-Per-Sec-FiveMin: 0
            Session-Since-Startup: 34
            Session-Peak-Max: 4
            Session-Peak-FiveMin: 0
            Idle-CPU: 98.700000""")
        self.send_fake_event_plain(event_plain)
        self.assertTrue(self.esl.heartbeat)

    def test_event_socket_data(self):
        """Should call registered handler for events."""
        self.log = False

        def on_log(event):
            self.log = True
        self.esl.register_handle('log', on_log)
        event_plain = dedent("""\
            Content-Type: log/data
            Content-Length: 126
            Log-Level: 7
            Text-Channel: 3
            Log-File: switch_core_state_machine.c
            Log-Func: switch_core_session_destroy_state
            Log-Line: 710
            User-Data: 4c882cc4-cd02-11e6-8b82-395b501876f9

            2016-12-28 10:34:08.398763 [DEBUG] switch_core_state_machine.c:710 (sofia/internal/7071@devitor) State DESTROY going to sleep
""")
        self.send_fake_raw_event_plain(event_plain)
        self.assertTrue(self.log)

    def test_event_with_multiline_channel_variables_content(self):
        """Should not break parse from ESL Event when."""
        def on_channel_create(self, event):
            self.channel_create = True
            self.parsed_event = event

        self.esl.channel_create = False
        self.esl.parsed_event = None
        self.esl.on_channel_create = types.MethodType(
            on_channel_create, self.esl)

        self.esl.register_handle('CHANNEL_CREATE', self.esl.on_channel_create)
        event_plain = dedent("""\
            Event-Name: CHANNEL_CREATE
            Core-UUID: ed56dab6-a6fc-11e4-960f-6f83a2e5e50a
            FreeSWITCH-Hostname: evoluxdev
            FreeSWITCH-Switchname: evoluxdev
            FreeSWITCH-IPv4: 172.16.7.69
            FreeSWITCH-IPv6: ::1
            Event-Date-Local: 2015-01-28 15:00:44
            Event-Date-GMT: Wed, 28 Jan 2015 18:00:44 GMT
            Event-Date-Timestamp: 1422468044671081
            Event-Calling-File: switch_core_state_machine.c
            Event-Calling-Function: switch_core_session_run
            Event-Calling-Line-Number: 509
            Event-Sequence: 3372
            Channel-State: CS_INIT
            Channel-Call-State: DOWN
            Channel-State-Number: 2
            Channel-Name: sofia/internal/100@192.168.50.4
            Unique-ID: d0b1da34-a727-11e4-9728-6f83a2e5e50a
            Call-Direction: inbound
            Presence-Call-Direction: inbound
            Channel-HIT-Dialplan: true
            Channel-Presence-ID: 100@192.168.50.4
            Channel-Call-UUID: d0b1da34-a727-11e4-9728-6f83a2e5e50a
            Answer-State: ringing
            Caller-Direction: inbound
            Caller-Logical-Direction: inbound
            Caller-Username: 100
            Caller-Dialplan: XML
            Caller-Caller-ID-Name: edev - 100
            Caller-Caller-ID-Number: 100
            Caller-Orig-Caller-ID-Name: edev - 100
            Caller-Orig-Caller-ID-Number: 100
            Caller-Network-Addr: 192.168.50.1
            Caller-ANI: 100
            Caller-Destination-Number: 101
            Caller-Unique-ID: d0b1da34-a727-11e4-9728-6f83a2e5e50a
            Caller-Source: mod_sofia
            Caller-Context: out-extensions
            Caller-Channel-Name: sofia/internal/100@192.168.50.4
            Caller-Profile-Index: 1
            Caller-Profile-Created-Time: 1422468044671081
            Caller-Channel-Created-Time: 1422468044671081
            Caller-Channel-Answered-Time: 0
            Caller-Channel-Progress-Time: 0
            Caller-Channel-Progress-Media-Time: 0
            Caller-Channel-Hangup-Time: 0
            Caller-Channel-Transfer-Time: 0
            Caller-Channel-Resurrect-Time: 0
            Caller-Channel-Bridged-Time: 0
            Caller-Channel-Last-Hold: 0
            Caller-Channel-Hold-Accum: 0
            Caller-Screen-Bit: true
            Caller-Privacy-Hide-Name: false
            Caller-Privacy-Hide-Number: false
            variable_direction: inbound
            variable_uuid: d0b1da34-a727-11e4-9728-6f83a2e5e50a
            variable_call_uuid: d0b1da34-a727-11e4-9728-6f83a2e5e50a
            variable_session_id: 9
            variable_sip_from_user: 100
            variable_sip_from_uri: 100@192.168.50.4
            variable_sip_from_host: 192.168.50.4
            variable_channel_name: sofia/internal/100@192.168.50.4
            variable_sip_call_id: 6bG.Hj5UCe8pDFEy1R9FO8EIfHtKrZ3H
            variable_ep_codec_string: GSM@8000h@20i@13200b,PCMU@8000h@20i@64000b,PCMA@8000h@20i@64000b,G722@8000h@20i@64000b
            variable_sip_local_network_addr: 192.168.50.4
            variable_sip_network_ip: 192.168.50.1
            variable_sip_network_port: 58588
            variable_sip_received_ip: 192.168.50.1
            variable_sip_received_port: 58588
            variable_sip_via_protocol: udp
            variable_sip_authorized: true
            variable_Event-Name: REQUEST_PARAMS
            variable_Core-UUID: ed56dab6-a6fc-11e4-960f-6f83a2e5e50a
            variable_FreeSWITCH-Hostname: evoluxdev
            variable_FreeSWITCH-Switchname: evoluxdev
            variable_FreeSWITCH-IPv4: 172.16.7.69
            variable_FreeSWITCH-IPv6: ::1
            variable_Event-Date-Local: 2015-01-28 15:00:44
            variable_Event-Date-GMT: Wed, 28 Jan 2015 18:00:44 GMT
            variable_Event-Date-Timestamp: 1422468044671081
            variable_Event-Calling-File: sofia.c
            variable_Event-Calling-Function: sofia_handle_sip_i_invite
            variable_Event-Calling-Line-Number: 8539
            variable_Event-Sequence: 3368
            variable_sip_number_alias: 100
            variable_sip_auth_username: 100
            variable_sip_auth_realm: 192.168.50.4
            variable_number_alias: 100
            variable_requested_domain_name: 192.168.50.4
            variable_record_stereo: true
            variable_transfer_fallback_extension: operator
            variable_toll_allow: celular_ddd,celular_local,fixo_ddd,fixo_local,ligar_para_outro_ramal,ramais_evolux_office
            variable_evolux_cc_position: 100
            variable_user_context: out-extensions
            variable_accountcode: dev
            variable_callgroup: dev
            variable_effective_caller_id_name: Evolux 100
            variable_effective_caller_id_number: 100
            variable_outbound_caller_id_name: Dev
            variable_outbound_caller_id_number: 0000000000
            variable_user_name: 100
            variable_domain_name: 192.168.50.4
            variable_sip_from_user_stripped: 100
            variable_sip_from_tag: ocZZPAo1FTdXA10orlmCaYeqc4mzYem1
            variable_sofia_profile_name: internal
            variable_recovery_profile_name: internal
            variable_sip_full_via: SIP/2.0/UDP 172.16.7.70:58588;rport=58588;branch=z9hG4bKPj-0Wi47Dyiq1mz3t.Bm8aluRrPEHF7-6C;received=192.168.50.1
            variable_sip_from_display: edev - 100
            variable_sip_full_from: "edev - 100" <sip:100@192.168.50.4>;tag=ocZZPAo1FTdXA10orlmCaYeqc4mzYem1
            variable_sip_full_to: <sip:101@192.168.50.4>
            variable_sip_req_user: 101
            variable_sip_req_uri: 101@192.168.50.4
            variable_sip_req_host: 192.168.50.4
            variable_sip_to_user: 101
            variable_sip_to_uri: 101@192.168.50.4
            variable_sip_to_host: 192.168.50.4
            variable_sip_contact_params: ob
            variable_sip_contact_user: 100
            variable_sip_contact_port: 58588
            variable_sip_contact_uri: 100@192.168.50.1:58588
            variable_sip_contact_host: 192.168.50.1
            variable_rtp_use_codec_string: G722,PCMA,PCMU,GSM,G729
            variable_sip_user_agent: Telephone 1.1.4
            variable_sip_via_host: 172.16.7.70
            variable_sip_via_port: 58588
            variable_sip_via_rport: 58588
            variable_max_forwards: 70
            variable_presence_id: 100@192.168.50.4
            variable_switch_r_sdp: v=0
            o=- 3631463817 3631463817 IN IP4 172.16.7.70
            s=pjmedia
            b=AS:84
            t=0 0
            a=X-nat:0
            m=audio 4016 RTP/AVP 103 102 104 109 3 0 8 9 101
            c=IN IP4 172.16.7.70
            b=AS:64000
            a=rtpmap:103 speex/16000
            a=rtpmap:102 speex/8000
            a=rtpmap:104 speex/32000
            a=rtpmap:109 iLBC/8000
            a=fmtp:109 mode=30
            a=rtpmap:3 GSM/8000
            a=rtpmap:0 PCMU/8000
            a=rtpmap:8 PCMA/8000
            a=rtpmap:9 G722/8000
            a=rtpmap:101 telephone-event/8000
            a=fmtp:101 0-15
            a=rtcp:4017 IN IP4 172.16.7.70

            variable_endpoint_disposition: DELAYED NEGOTIATION""")
        self.send_fake_event_plain(event_plain)
        self.assertTrue(self.esl.channel_create)

        expected_variable_value = dedent("""\
            v=0
            o=- 3631463817 3631463817 IN IP4 172.16.7.70
            s=pjmedia
            b=AS:84
            t=0 0
            a=X-nat:0
            m=audio 4016 RTP/AVP 103 102 104 109 3 0 8 9 101
            c=IN IP4 172.16.7.70
            b=AS:64000
            a=rtpmap:103 speex/16000
            a=rtpmap:102 speex/8000
            a=rtpmap:104 speex/32000
            a=rtpmap:109 iLBC/8000
            a=fmtp:109 mode=30
            a=rtpmap:3 GSM/8000
            a=rtpmap:0 PCMU/8000
            a=rtpmap:8 PCMA/8000
            a=rtpmap:9 G722/8000
            a=rtpmap:101 telephone-event/8000
            a=fmtp:101 0-15
            a=rtcp:4017 IN IP4 172.16.7.70""")
        self.assertEqual(self.esl.parsed_event.headers['variable_switch_r_sdp'],
                         expected_variable_value)

    def test_api_response(self):
        """Should properly read api response from ESL."""
        response = self.esl.send('api khomp show links concise')
        self.assertEqual('api/response', response.headers['Content-Type'])
        self.assertIn('Content-Length', response.headers)
        self.assertEqual(len(response.data),
                         int(response.headers['Content-Length']))

    def test_command_not_found(self):
        """Should properly read command response from ESL."""
        response = self.esl.send('unknown_command')
        self.assertEqual('command/reply', response.headers['Content-Type'])
        self.assertEqual('-ERR command not found',
                         response.headers['Reply-Text'])

    def test_event_without_handler(self):
        """Should not break if receive an event without handler."""
        self.send_fake_event_plain('Event-Name: EVENT_UNKNOWN')
        self.assertTrue(self.esl.connected)
