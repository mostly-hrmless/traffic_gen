#!/usr/bin/env python
import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import *
import sys
import time
import random
import datetime
import argparse
import HTTPRequestData
import HTTPResponseData
import SMTPData
import sentences
import signal

total_bytes = 0
total_packets = 0
start = 0

clients = [
            '192.168.2.31',
            '192.168.2.32',
            '192.168.2.33',
            '192.168.2.34',
            '192.168.2.35',
            '192.168.2.36',
            '192.168.2.37',
          ]

servers = [
	    '11.11.11.11',
	    '22.22.22.22',
            '33.33.33.33',
            '44.44.44.44',
	    '55.55.55.55',
          ]

dns_servers = [
            '8.8.8.8',
            '8.8.2.2',
          ]

mail_servers = [
            '9.9.9.9'
            '10.10.10.10',
          ]


class GenerateEmail(object):
  def __init__(self):
    pass
  def GenEmail(self):
    self.email = ''
    self.OutputEmail(self.makeEmail())
    return self.email
  def makeEmail(self):
    yield random.choice(SMTPData.greetings)
    yield '\n'
    yield self.body()
    yield '\r\n.'
  def body(self):
    yield self.paragraph()
    if random.random() < .50:
      yield self.body()
  def paragraph(self):
    yield '\n'
    for _ in xrange(random.randrange(3, 10)):
      yield self.sentence()
  def sentence(self):
    yield random.choice(sentences.sentences)
  def OutputEmail(self, generator):
    if isinstance(generator, str):
      self.email += generator
    else:
      for g in generator: self.OutputEmail(g)


class GenerateSMTPData(object):
  def __init__(self):
    self.GenEmail = GenerateEmail()
  def getBanner(self):
    return random.choice(SMTPData.Banners)
  def getRandom(self, length):
    return ''.join(random.choice(string.ascii_letters) for _ in xrange(length))
  def getAddr(self):
    return self.getRandom(8) + "@" + self.getRandom(8) + ".com"
  def getMail(self, fromAddr, toAddr):
    mail = str(self.GenEmail.GenEmail())
    header = """From: <%(from)s>
To: <%(to)s>
Subject: %(subject)s
Date: %(date)s
Message-ID: <%(random)s>
Content-Language: en-us\r\n\r\n
""" % { 'from': fromAddr, 'to': toAddr, 'subject': random.choice(sentences.sentences),
        'date': datetime.datetime.utcnow().strftime("%a, %w %b %Y %H:%M:%S GMT"),
        'random': self.getRandom(32)  }
    return header + mail

class GenerateHTMLData(object):
  def __init__(self):
    pass
  def GenHTML(self):
    self.html = ''
    self.OutputHTML(self.makeHTMLDoc())
    return self.html
  def makeHTMLDoc(self):
    yield '<!DOCTYPE html>\n'
    yield '<html lang="en">\n'
    yield ' <head><title>'
    yield self.sentence()
    yield ' </title></head>\n'
    yield ' <body>'
    yield self.body()
    yield '\n </body>\n'
    yield '</html>'
  def body(self):
    yield self.section()
    if random.random() < .50:
      yield self.body()
  def section(self):
    yield '\n\n<h1>'
    yield self.sentence()
    yield '</h1>\n<p>'
    for _ in xrange(random.randrange(3, 15)):
      yield self.sentence()
  def sentence(self):
    yield random.choice(sentences.sentences)
  def word(self):
    return ''.join(random.choice(string.ascii_lowercase) for _ in xrange(random.randrange(2,10)))
  def OutputHTML(self, generator):
    if isinstance(generator, str):
      self.html += generator
    else:
      for g in generator: self.OutputHTML(g)

class GenerateHTTPData(object):
  def __init__(self):
    self.GenHTML = GenerateHTMLData()
  def getRequest(self):
    chance = random.random()
    if chance < .25:
      return random.choice(HTTPRequestData.GET)
    else:
      return self.makeReqHeader()
  def makeReqHeader(self):
    return """GET %(uri)s HTTP/1.1
Host: %(domain)s.com
Connection: keep-alive
Cache-Control: max-age=0
Accept: */*
User-Agent: %(ua)s
Accept-Language: en-US,en;q=0.8\r\n\r\n
""" % { 'domain': ''.join(random.choice(string.ascii_lowercase) for _ in xrange(random.randrange(2,10))),
        'uri': random.choice(HTTPRequestData.URI), 'ua':  random.choice(HTTPRequestData.UA) }
  def getResponse(self):
    chance = random.random()
    if chance < .25:
      return random.choice(HTTPResponseData.RESPONSE)
    else:
      return self.makeResponse()
  def makeResponse(self):
    html = str(self.GenHTML.GenHTML())
    header = """HTTP/1.1 200 OK
Date: %(date)s
Content-Type: text/html
Content-Length: %(length)s
Server: %(server)s

""" % { 'date': datetime.datetime.utcnow().strftime("%a, %w %b %Y %H:%M:%S GMT"),
        'length': len(html), 'server': random.choice(HTTPResponseData.Server) }
    return header + html


class TrafficSession(object):
  def __init__(self):
    self.packets = []
    self.client = self.server = ''
    self.clientSeq = self.serverSeq = 0
    self.GenHTTP = GenerateHTTPData()
    self.GenSMTP = GenerateSMTPData()
  def getPacket(self):
    if not self.packets:
      self.makeNext()
    return self.packets.pop(0)
  def makeNext(self):
    chance = random.random()
    if chance < .50:
      #print('HTTP')
      self.makeHTTP()
    elif chance < .90:
      #print('SMTP')
      self.makeSMTP()
    else:
      #print('DNS')
      self.makeDNS()
  def makeSMTP(self):
    self.client = random.choice(clients)
    self.server = random.choice(mail_servers)
    self.clientPort = random.randrange(1024,65535);
    self.serverPort = 25;

    self.makeTCPStart(25)

    fromAddr = self.GenSMTP.getAddr();
    toAddr   = self.GenSMTP.getAddr();
    self.sendSingleFromServer(self.GenSMTP.getBanner() + "\r\n")
    self.sendSingleFromClient("EHLO " + random.choice(HTTPRequestData.domain) + "\r\n")
    self.sendSingleFromServer("250- Hello [" + random.choice(clients) + "]\r\n250 HELP\r\n")
    self.sendSingleFromClient("AUTH LOGIN\r\n")
    self.sendSingleFromServer("334 " + self.GenSMTP.getRandom(12) + "\r\n")
    self.sendSingleFromClient(self.GenSMTP.getRandom(28) + "\r\n")
    self.sendSingleFromServer("334 " + self.GenSMTP.getRandom(12) + "\r\n")
    self.sendSingleFromClient(self.GenSMTP.getRandom(14) + "==" + "\r\n")
    self.sendSingleFromServer("235 Authentication succeeded\r\n")
    self.sendSingleFromClient("MAIL FROM: " + fromAddr + "\r\n")
    self.sendSingleFromServer("250 OK\r\n")
    self.sendSingleFromClient("RCPT FROM: " + toAddr + "\r\n")
    self.sendSingleFromServer("250 Accepted\r\n")
    self.sendSingleFromClient("DATA\r\n")
    self.sendSingleFromServer("354 Enter message, ending with \".\" on a line by itself\r\n")

    n = 1460
    data = self.GenSMTP.getMail(fromAddr, toAddr) + "\r\n"
    dataChunks = [data[i:i+n] for i in range(0, len(data), n)]
    for i, chunk in enumerate(dataChunks):
      self.sendSingleFromClient(chunk)

    self.sendSingleFromServer("250 OK\r\n")
    self.sendSingleFromClient("QUIT\r\n")
    self.sendSingleFromServer("221 closing connection\r\n")
    self.makeTCPStop()

  def makeDNS(self):
    self.client = random.choice(clients)
    self.server = random.choice(dns_servers)
    self.clientPort = random.randrange(1024,65535);
    self.serverPort = 53;

    choice = random.random()
    if choice < .75:
      dns_query = random.choice(HTTPRequestData.domain)
    else:
      dns_query = ''.join(random.choice(string.ascii_lowercase) for _ in xrange(random.randrange(2,10))) + ".com"

    query = Ether(type=0x0800)/IP(src=self.client,dst=self.server)/\
            UDP(sport=self.clientPort,dport=self.serverPort)/\
            DNS(id=random.randrange(0,65535),rd=1,qd=DNSQR(qname=dns_query))
    response = Ether(type=0x0800)/IP(src=self.server,dst=self.client)/\
               UDP(dport=self.clientPort,sport=self.serverPort)/\
               DNS(id=query[DNS].id,qd=query[DNS].qd,aa=1,qr=1,\
                   an=DNSRR(rrname=query[DNS].qd.qname,ttl=10,type="A",rclass="IN",rdata=random.choice(servers)))
    self.packets.append(query)
    self.packets.append(response)
  def makeHTTP(self):
    self.makeTCPStart(80)
    self.sendData(self.GenHTTP.getRequest(), True)
    self.sendData(self.GenHTTP.getResponse(), False)
    self.makeTCPStop()
  def makeTCPStart(self, port):
    self.client = random.choice(clients)
    self.server = random.choice(servers)
    self.clientPort = random.randrange(1024,65535);
    self.serverPort = port;
    self.clientSeq = random.randrange(0, math.pow(2,32))
    self.serverSeq = random.randrange(0, math.pow(2,32))

    self.packets.append(Ether(type=0x0800)/IP(src=self.client,dst=self.server)/
      TCP(sport=self.clientPort,dport=self.serverPort,flags="S",seq=self.clientSeq))
    self.clientSeq += 1
    self.packets.append(Ether(type=0x0800)/IP(dst=self.client,src=self.server)/
      TCP(dport=self.clientPort,sport=self.serverPort,flags="SA",seq=self.serverSeq,ack=self.clientSeq))
    self.serverSeq += 1
    self.packets.append(Ether(type=0x0800)/IP(src=self.client,dst=self.server)/
      TCP(sport=self.clientPort,dport=self.serverPort,flags="A",seq=self.clientSeq,ack=self.serverSeq))

  def makeTCPStop(self):
    self.packets.append(Ether(type=0x0800)/IP(src=self.client,dst=self.server)/
      TCP(sport=self.clientPort,dport=self.serverPort,flags="FA",seq=self.clientSeq,ack=self.serverSeq))
    self.clientSeq += 1
    self.packets.append(Ether(type=0x0800)/IP(dst=self.client,src=self.server)/
      TCP(dport=self.clientPort,sport=self.serverPort,flags="FA",seq=self.serverSeq,ack=self.clientSeq))
    self.serverSeq += 1
    self.packets.append(Ether(type=0x0800)/IP(src=self.client,dst=self.server)/
      TCP(sport=self.clientPort,dport=self.serverPort,flags="A",seq=self.clientSeq,ack=self.serverSeq))
  def sendData(self, data, fromClient):
    if fromClient:
      srcIP   = self.client
      srcPort = self.clientPort
      srcSeq  = self.clientSeq
      dstIP   = self.server
      dstPort = self.serverPort
      dstSeq  = self.serverSeq
      self.clientSeq += len(data)
    else:
      srcIP   = self.server
      srcPort = self.serverPort
      srcSeq  = self.serverSeq
      dstIP   = self.client
      dstPort = self.clientPort
      dstSeq  = self.clientSeq
      self.serverSeq += len(data)

    tcpFlags = "A"
    n = 1460
    dataChunks = [data[i:i+n] for i in range(0, len(data), n)]
    for i, chunk in enumerate(dataChunks):
      if i == (len(dataChunks) - 1):
        tcpFlags = "PA"
      self.packets.append(Ether(type=0x0800)/IP(src=srcIP,dst=dstIP)/
        TCP(sport=srcPort,dport=dstPort,flags=tcpFlags,seq=srcSeq,ack=dstSeq)/
        Raw(load=chunk))
      srcSeq += len(chunk)
      self.packets.append(Ether(type=0x0800)/IP(dst=srcIP,src=dstIP)/
        TCP(dport=srcPort,sport=dstPort,flags="A",seq=dstSeq,ack=srcSeq))
  def sendSingleFromClient(self,data):
    self.packets.append(Ether(type=0x0800)/IP(src=self.client,dst=self.server)/
      TCP(sport=self.clientPort,dport=self.serverPort,flags="PA",seq=self.clientSeq,ack=self.serverSeq)/
      Raw(load=data))
    self.clientSeq += len(data)
  def sendSingleFromServer(self,data):
    self.packets.append(Ether(type=0x0800)/IP(src=self.server,dst=self.client)/
      TCP(sport=self.serverPort,dport=self.clientPort,flags="PA",seq=self.serverSeq,ack=self.clientSeq)/
      Raw(load=data))
    self.serverSeq += len(data)


def generate_traffic(sessions, writer, socket, max_pkt_count, max_byte_count, delay, loop):
  """
  Main traffic generation loop
  """
  global total_packets
  global total_bytes
  global start

  start = time.clock()

  while loop or total_packets < max_pkt_count or total_bytes < max_byte_count:
    upnext = random.choice(sessions).getPacket();
    total_bytes += len(upnext)
    if writer is None:
      if socket is None:
        sendp(upnext, verbose=0)
      else:
        socket.send(upnext)
    else:
      writer.write(upnext)
    total_packets += 1
    if delay:
      time.sleep(delay)


def printTotals():
  global total_packets
  global total_bytes
  global start
  elapsed = time.clock() - start
  print "Total bytes sent:\t",  total_bytes
  print "Total packets sent:\t", total_packets
  print "Total time elapsed:\t", elapsed
  print "Average Packets/sec:\t", total_packets/elapsed
  print "Average bytes/sec:\t", total_bytes/elapsed

def handler(signal, frame):
  printTotals()
  sys.exit(0)

def main(argv=None):

  parser = argparse.ArgumentParser()
  parser.add_argument('-f', '--filename', dest='filename', help='filename for pcap')
  parser.add_argument('-d', '--delay', dest='delay', type=float, default=0,
                      help='delay between sending packets')
  parser.add_argument('-s', '--sessions', dest='sessions', type=int, default=10,
                      help='number of concurrent traffic sessions')
  parser.add_argument('-p', '--numpackets', type=int, default=0, dest='num_packets',
                      help='number of packets to send')
  parser.add_argument('-m', '--mbytes', type=int, default=0, dest='num_mbytes',
                      help='number of megabytes to send')
  parser.add_argument('-i', '--interface', help='set layer 2 interface')
  parser.add_argument('--loop', default=False, action='store_true',
                      help='loop forever')
  args= parser.parse_args()

  random.seed()
  signal.signal(signal.SIGINT, handler)

  if args.num_mbytes:
    args.num_mbytes *= 1024 * 1024

  socket = None
  if args.interface is not None:
    s = conf.L2socket(iface=args.interface)

  SessionList = []
  for count in xrange(args.sessions):
    x = TrafficSession()
    x.attr = count
    SessionList.append(x)

  writer = None
  if args.filename is not None:
    writer = PcapWriter(args.filename, append=True)
  else:
    print "Write to interface"

  generate_traffic(SessionList, writer, socket, args.num_packets,
                   args.num_mbytes, args.delay, args.loop)

  if writer is not None:
    writer.close()

  return 0


if __name__ == '__main__':
  status = main()
  printTotals()
  sys.exit(status)

